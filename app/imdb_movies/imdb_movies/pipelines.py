import json
from os import path
from scrapy import Spider
from imdb_movies.items import ImdbMoviesItem
from imdb_movies.enum_model import ConfigImdb, ConfigDB, RefineLevel
from imdb_movies.imdb_refine import CreatorOutputData
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from imdb_movies.models_patterns.movie_factory import MovieFactory
from imdb_movies.models_patterns.error_handlers import retry_with_backoff, RetryConfig
from imdb_movies.models_patterns.database_strategies import DatabaseStrategyFactory


def get_database_strategy(logger: Spider = None):
    db_type = ConfigDB.DB.value.lower()
    return DatabaseStrategyFactory.create_strategy(db_type, logger)

def save_to_json_file(data: list[dict], output_path: str) -> None:
    """Guarda datos en formato JSON en un archivo."""
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except (OSError, IOError) as e:
        print(f"Error al guardar el archivo JSON: {e}")


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

        if spider.refine == RefineLevel.INTERMEDIATE.value:
            return

        save_to_json_file(self.items, self.input_document_json_path)

        if spider.refine ==  RefineLevel.BASIC.value:
            spider.logger.info('- Proceso de extracción finalizado')
            return

        spider.logger.info('- Procesando archivo JSON...')
    
        try:
            strategy = get_database_strategy(spider.logger)
            session = strategy.get_session()

            creator_output_data = CreatorOutputData(
                document_json_path=self.input_document_json_path,
                document_csv_path=self.output_document_json_path,
                logger=spider.logger
            )

            df_output = creator_output_data.refine_output_data()

            for _, row in df_output.iterrows():
                try:
                    movie = MovieFactory.create_movie_from_row(row)
                    session.add(movie)
                except Exception as row_error:
                    spider.logger.error(f"❌ Error procesando fila: {row_error}")

            self._commit_with_retry(session, spider.logger)
            spider.logger.info('Guardado exitoso de modelos Movie y Actor.')

            print('\n' + '🎉' * 60)
            print('✅ ¡IMDB SCRAPER COMPLETADO EXITOSAMENTE!')
            print('🎬 Películas y actores guardados correctamente en la base de datos.')
            print('🎉' * 60 + '\n')

        except Exception as error:
            spider.logger.error(f'❌ Error general en refinado o guardado a modelos: {error}')
            session.rollback()
        finally:
            session.close()

    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=2.0),
        retry_on=(SQLAlchemyError, DisconnectionError)
    )
    def _commit_with_retry(self, session: Session, logger):
        logger.info('Intentando commit a la base de datos...')
        session.commit()