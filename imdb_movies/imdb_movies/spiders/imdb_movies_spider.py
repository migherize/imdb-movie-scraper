import os
import re
import scrapy
from pathlib import Path
from ast import literal_eval
from scrapy.http import Response
from imdb_movies.items import ImdbMoviesItem
from imdb_movies.enum_model import ConfigImdb


class ImdbMoviesSpiderSpider(scrapy.Spider):
    name = "imdb_movies_spider"

    def __init__(self, refine=2, *args, **kwargs):
        super(ImdbMoviesSpiderSpider).__init__(*args, **kwargs)
        self.refine = int(refine)
        Path(ConfigImdb.DATA_PATH.value).mkdir(parents=True, exist_ok=True)

    def start_requests(self):

        if self.refine == 1:
            self.logger.info('Ejecucion de proceso de refinado')
            return []

        start_url = ConfigImdb.TOP_MOVIE_URL.value
        return [
            scrapy.Request(
                url=start_url,
                headers=ConfigImdb.HEADERS.value,
                cookies=ConfigImdb.COOKIES.value,
                callback=self.parse
            )
        ]

    def parse(self, response: Response):

        """ Pagina con las 250 peliculas """

        info_movies = response.xpath(ConfigImdb.XPATH_JSON_INFO.value).get()
        if info_movies is None:
            self.logger.warning("No se encontraron datos de peliculas en la pagina.")
            return
        
        info_movies = literal_eval(info_movies)
        if not info_movies:
            self.logger.error('No se obtuvo informacion de todas las peliculas')
            return None
        
        info_movies: list[dict] = info_movies.get("itemListElement", [])

        for index, info_movie in enumerate(info_movies):

            if index == 50:
                break

            output_info_movie = self._get_info_movie_from_top_movies(info_movie.get('item', {}))
            if output_info_movie["movie_url"] == '':
                self.logger.warning('%s no cuenta con una url', output_info_movie['title'])
                continue

            yield scrapy.Request(
                url=output_info_movie["movie_url"],
                headers=ConfigImdb.HEADERS.value,
                cookies=ConfigImdb.COOKIES.value,
                callback=self.parse_main_info_movie,
                dont_filter=True,
                meta={'output_info_movie': output_info_movie}
            )

    def parse_main_info_movie(self, response: Response):
        
        """ Informacion de la pelicula  """
        
        output_info_movie = response.meta.get('output_info_movie')
        item = ImdbMoviesItem()

        info_movie = response.xpath(ConfigImdb.XPATH_JSON_INFO.value).get()
        if not info_movie:
            self.logger.warning(
                '%s no cuenta con informacion en el json en la pagina principal', 
                output_info_movie['title']
            )
            item['info_movie'] = output_info_movie
            yield item
            return None

        info_movie = literal_eval(info_movie)
        if not info_movie:
            self.logger.error('No se obtuvo informacion de %s', output_info_movie['title'])
            item['info_movie'] = output_info_movie
            yield item
            return None

        info_movie: dict
        output_info_movie['date_published'] = info_movie.get('datePublished', '')
        output_info_movie['actors'] = self._get_actors(info_movie.get('actor', [{}]))
        output_info_movie['metascore'] = self._get_metascore(response.text)

        item['info_movie'] = output_info_movie
        yield item


    def _get_info_movie_from_top_movies(self, info_movie: dict[str, str | dict]) -> dict[str, str | list]:
        return {
            'title': info_movie.get('name', ''),
            'alternate_title': info_movie.get('alternateName', ''),
            'rating': info_movie.get('aggregateRating', {}).get('ratingValue', ''),
            'duration': info_movie.get('duration', ''),
            'movie_url': info_movie.get('url', ''),
            'movie_id': self._get_movie_id(info_movie.get('url', '')),
            'date_published': '',
            'actors': [],
            'metascore': ''
        }

    def _get_movie_id(self, url: str) -> str:
        return list(filter(None, url.split('/')))[-1]
    

    def _get_actors(self, actors: list[dict]) -> list[str]:
        return [inf_actor.get('name', '') for inf_actor in actors]

    def _get_metascore(self, body_text: str) -> str:
        return (
            re.search(r'\"score\":([\d.]+)', body_text).group(1) 
            if re.search(r'\"score\":([\d.]+)', body_text) 
            else ''
        )
