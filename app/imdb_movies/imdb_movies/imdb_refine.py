
import json
import isodate
import pandas as pd
from logging import Logger
from imdb_movies.enum_model import ConfigRefine
from os import path


class CreatorOutputData:

    def __init__(self, **kwargs):
        self.document_json_path: None | str = kwargs.get('document_json_path', None)
        self.output_document_csv_path: None | str = kwargs.get('document_csv_path', None)
        self.logger: Logger = kwargs.get('logger')

    def refine_output_data(self) -> pd.DataFrame:
        movies_data = self._read_json(self.document_json_path)
        if not movies_data:
            self.logger.warning(f'El archivo {self.document_json_path} esta vacio o no existe')
            return None
        input_to_dataframe = [movie.get('info_movie', {}) for movie in  movies_data] 
        df = pd.DataFrame(input_to_dataframe)
        df = df.astype(ConfigRefine.DATA_TYPE.value)
        df["date_published"] = pd.to_datetime(df["date_published"], errors="coerce")
        df["duration_minutes"] = df["duration"].apply(self._parse_duration)
        df[ConfigRefine.OUTPUT_COLUMNS.value].to_csv(
            self.output_document_csv_path, 
            index=False, 
            encoding='utf-8'
        )
        return df

    def _read_json(self, document_json_path: str) -> list[dict]:
        data = []
        try:
            if path.exists(document_json_path):
                with open(document_json_path, 'r') as document_json:
                    data = json.load(document_json)
        except Exception as error:
            self.logger.warning("Existe problemas para leer el archivo json. Error:", error)
        return data


    def _parse_duration(self, date: str) -> None | float:
        try:
            duration = isodate.parse_duration(date)
            return duration.total_seconds() / 60
        except Exception as error:
            self.logger.warning(
                'Error al momento de parsear la fecha: %s. Error: %s', 
                [date], 
                error
            )
            return None
