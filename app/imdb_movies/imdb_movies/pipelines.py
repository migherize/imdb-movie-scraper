import json
import ast
from os import path
from scrapy import Spider
from imdb_movies.items import ImdbMoviesItem
from imdb_movies.enum_model import ConfigImdb, ConfigDB
from imdb_movies.imdb_refine import CreatorOutputData
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from imdb_movies.models_patterns.models import Movie, Actor

class ImdbMoviesPipeline:

    def open_spider(self, spider: Spider):
        spider.logger.info('- Inicio del spider: %s', spider.name)
        self.items = []
        self.input_document_json_path = path.join(
            ConfigImdb.DATA_PATH.value, ConfigImdb.OUTPUT_DOCUMENT_NAME_PAGE.value
        )
        self.output_document_json_path = path.join(
            ConfigImdb.DATA_PATH.value, ConfigImdb.OUTPUT_DOCUMENT_NAME_REFINE.value
        )


    def process_item(self, item: ImdbMoviesItem, spider: Spider):
        self.items.append(dict(item))
        return item
    
    def close_spider(self, spider: Spider):

        spider.logger.info('- Finalizada la ejecución del spider: %s', spider.name)

        if spider.refine == 1:
            pass
        else:
            save_to_json_file(self.items, self.input_document_json_path)

        if spider.refine == 0:
            spider.logger.info('- Proceso de extracción finalizado')
            return

        spider.logger.info('- Procesando archivo JSON...')

        try:
            creator_output_data = CreatorOutputData(
                document_json_path=self.input_document_json_path,
                document_csv_path=self.output_document_json_path,
                logger=spider.logger
            )

            df_output = creator_output_data.refine_output_data()

            engine = create_engine(ConfigDB.DATABASE_URL.value)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()

            for _, row in df_output.iterrows():
                try:
                    title = row['title']
                    year = int(str(row['date_published'])[:4]) if row['date_published'] else None
                    rating = float(row['rating']) if row['rating'] else None
                    duration = int(row['duration_minutes']) if row['duration_minutes'] else None
                    metascore = float(row['metascore']) if row['metascore'] else None
                    actors_raw = row['actors']

                    movie = Movie(
                        title=title,
                        year=year,
                        rating=rating,
                        duration=duration,
                        metascore=metascore
                    )

                    actor_names = []
                    if actors_raw:
                        if isinstance(actors_raw, list):
                            actor_names = actors_raw
                        elif isinstance(actors_raw, str):
                            try:
                                actor_names = ast.literal_eval(actors_raw)
                                if not isinstance(actor_names, list):
                                    raise ValueError
                            except Exception:
                                actor_names = [a.strip() for a in actors_raw.split(';')]

                    movie.actors = [Actor(name=a) for a in actor_names if a]

                    session.add(movie)

                except Exception as row_error:
                    spider.logger.error(f"❌ Error procesando fila: {row_error}")

            session.commit()

            print('\n' + '#' * 40)
            print('✅ Scrapy terminó exitosamente.')
            print('🎬 Películas y actores guardados correctamente en la base de datos.')
            print('#' * 40 + '\n')

            spider.logger.info('Guardado exitoso de modelos Movie y Actor.')

        except Exception as error:
            spider.logger.error(f'❌ Error general en refinado o guardado a modelos: {error}')
            session.rollback()
        finally:
            session.close()



def save_to_json_file(data: list[dict], output_path: str) -> None:
    """Guarda datos en formato JSON en un archivo."""
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except (OSError, IOError) as e:
        print(f"Error al guardar el archivo JSON: {e}")