import json
from os import path
from scrapy import Spider
from imdb_movies.items import ImdbMoviesItem
from imdb_movies.enum_model import ConfigImdb
from imdb_movies.imdb_refine import CreatorOutputData


class ImdbMoviesPipeline:

    def open_spider(self, spider: Spider):
        spider.logger.info('- Inicio del spider: %s', spider.name)
        self.items = []
        self.input_document_json_path = path.join(
            ConfigImdb.DATA_PATH.value, ConfigImdb.output_document_name_page.value
        )
        self.output_document_json_path = path.join(
            ConfigImdb.DATA_PATH.value, ConfigImdb.output_document_name_refine.value
        )


    def process_item(self, item: ImdbMoviesItem, spider: Spider):
        self.items.append(dict(item))
        return item
    
    def close_spider(self, spider: Spider):

        spider.logger.info('- Finalizada la ejecucion del spider: %s', spider.name)

        if spider.refine == 1:
            pass
        else:
            save_to_json_file(self.items, self.input_document_json_path)
        
        if spider.refine == 0:
            spider.logger.info('- Proceso de extraccion finalizado')
            return None

        spider.logger.info('- Procesando archivo json...')
        try:
            creator_output_data = CreatorOutputData(
                document_json_path=self.input_document_json_path,
                document_csv_path=self.output_document_json_path,
                logger=spider.logger
            )
            df_output = creator_output_data.refine_output_data()
            # TODO: Utilizar el df_output para cargar a la DB
            spider.logger.info('Proceso de refinado finalizado')

        except Exception as error:
            spider.logger.error('Existe problemas al ejecutar el creator. Error: %s', error)
            return None


def save_to_json_file(data: list[dict], output_path: str) -> None:
    """Guarda datos en formato JSON en un archivo."""
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except (OSError, IOError) as e:
        print(f"Error al guardar el archivo JSON: {e}")