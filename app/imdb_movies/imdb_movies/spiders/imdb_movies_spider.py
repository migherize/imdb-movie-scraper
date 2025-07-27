from logging import config
import os
import re
import scrapy
from pathlib import Path
from ast import literal_eval
from scrapy.http import Response
from imdb_movies.items import ImdbMoviesItem
from imdb_movies.enum_model import (
    ConfigDB,
    ConfigImdb,
    RefineLevel,
    MovieJsonKeys,
    OutputMovieKeys,
)


class ImdbMoviesSpiderSpider(scrapy.Spider):
    name = "imdb_movies_spider"

    def __init__(self, refine=RefineLevel.ADVANCED.value, *args, **kwargs):
        super(ImdbMoviesSpiderSpider).__init__(*args, **kwargs)
        self.refine = int(refine)
        Path(ConfigImdb.DATA_PATH.value).mkdir(parents=True, exist_ok=True)

    def start_requests(self):

        if self.refine == RefineLevel.INTERMEDIATE.value:
            self.logger.info("Ejecucion de proceso de refinado")
            return []

        start_url = ConfigImdb.TOP_MOVIE_URL.value
        return [
            scrapy.Request(
                url=start_url,
                headers=ConfigImdb.HEADERS.value,
                cookies=ConfigImdb.COOKIES.value,
                callback=self.parse,
            )
        ]

    def parse(self, response: Response):
        """Pagina con las 250 peliculas"""

        info_movies = response.xpath(ConfigImdb.XPATH_JSON_INFO.value).get()
        if info_movies is None:
            self.logger.warning("No se encontraron datos de peliculas en la pagina.")
            return

        info_movies = literal_eval(info_movies)
        if not info_movies:
            self.logger.error("No se obtuvo informacion de todas las peliculas")
            return None

        info_movies: list[dict] = info_movies.get("itemListElement", [])

        for index, info_movie in enumerate(info_movies):

            if index == ConfigImdb.TOTAL_SCRAPY.value:
                break

            output_info_movie = self._get_info_movie_from_top_movies(
                info_movie.get("item", {})
            )
            if output_info_movie["movie_url"] == "":
                self.logger.warning(
                    "%s no cuenta con una url", output_info_movie["title"]
                )
                continue

            yield scrapy.Request(
                url=output_info_movie["movie_url"],
                headers=ConfigImdb.HEADERS.value,
                cookies=ConfigImdb.COOKIES.value,
                callback=self.parse_main_info_movie,
                dont_filter=True,
                meta={"output_info_movie": output_info_movie},
            )

    def parse_main_info_movie(self, response: Response):
        """Extrae la información principal de una película desde la página de IMDb."""

        output_info_movie = response.meta.get("output_info_movie", {})
        item = ImdbMoviesItem()

        info_movie_raw = response.xpath(ConfigImdb.XPATH_JSON_INFO.value).get()
        title_fallback = output_info_movie.get(OutputMovieKeys.TITLE.value, "[Título desconocido]")

        if not info_movie_raw:
            self.logger.warning(
                "%s no cuenta con información JSON en la página principal",
                title_fallback,
            )
            item[OutputMovieKeys.INFO_MOVIE.value] = output_info_movie
            yield item
            return

        try:
            info_movie = literal_eval(info_movie_raw)
        except Exception as e:
            self.logger.error(
                "Error al evaluar JSON info_movie para %s: %s",
                title_fallback,
                str(e),
            )
            item[OutputMovieKeys.INFO_MOVIE.value] = output_info_movie
            yield item
            return

        if not info_movie:
            self.logger.error(
                "No se obtuvo información válida de %s",
                title_fallback,
            )
            item[OutputMovieKeys.INFO_MOVIE.value] = output_info_movie
            yield item
            return

        output_info_movie[OutputMovieKeys.DATE_PUBLISHED.value] = info_movie.get(
            MovieJsonKeys.DATE_PUBLISHED.value, ""
        )

        output_info_movie[OutputMovieKeys.ACTORS.value] = self._get_actors(
            info_movie.get(MovieJsonKeys.ACTOR.value, [{}])
        )

        output_info_movie[OutputMovieKeys.METASCORE.value] = self._get_metascore(response.text)

        item[OutputMovieKeys.INFO_MOVIE.value] = output_info_movie
        yield item

    def _get_info_movie_from_top_movies(self, info_movie: dict[str, str | dict]) -> dict[str, str | list]:
        return {
            OutputMovieKeys.TITLE.value: info_movie.get(MovieJsonKeys.NAME.value, ''),
            OutputMovieKeys.ALT_TITLE.value: info_movie.get(MovieJsonKeys.ALT_NAME.value, ''),
            OutputMovieKeys.RATING.value: info_movie.get(MovieJsonKeys.AGGREGATE_RATING.value, {}).get(MovieJsonKeys.RATING_VALUE.value, ''),
            OutputMovieKeys.DURATION.value: info_movie.get(MovieJsonKeys.DURATION.value, ''),
            OutputMovieKeys.MOVIE_URL.value: info_movie.get(MovieJsonKeys.URL.value, ''),
            OutputMovieKeys.MOVIE_ID.value: self._get_movie_id(info_movie.get(MovieJsonKeys.URL.value, '')),
            OutputMovieKeys.DATE_PUBLISHED.value: '',
            OutputMovieKeys.ACTORS.value: [],
            OutputMovieKeys.METASCORE.value: ''
        }

    def _get_movie_id(self, url: str) -> str:
        if not url:
            return ""
        parts = [segment for segment in url.split("/") if segment]
        return parts[-1] if parts else ""

    def _get_actors(self, actors: list[dict]) -> list[str]:
        return [actor.get("name", "") for actor in actors if actor.get("name")]

    def _get_metascore(self, body_text: str) -> str:
        return (
            re.search(r"\"score\":([\d.]+)", body_text).group(1)
            if re.search(r"\"score\":([\d.]+)", body_text)
            else ""
        )
