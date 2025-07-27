import json
import isodate
import pandas as pd
from os import path
from logging import Logger
from imdb_movies.enum_model import ConfigRefine


class CreatorOutputData:

    def __init__(self, **kwargs):
        self.document_json_path: str | None = kwargs.get('document_json_path')
        self.output_document_csv_path: str | None = kwargs.get('document_csv_path')
        self.logger: Logger = kwargs.get('logger')

    def refine_output_data(self) -> pd.DataFrame | None:
        movies_data = self._read_json_file(self.document_json_path)

        if not movies_data:
            self.logger.warning(
                "El archivo JSON '%s' está vacío o no se pudo leer.",
                self.document_json_path
            )
            return None

        df = pd.DataFrame([movie.get('info_movie', {}) for movie in movies_data])

        if df.empty:
            self.logger.warning("No se extrajo información válida desde el JSON.")
            return None

        try:
            df = df.astype(ConfigRefine.DATA_TYPE.value)
            df["date_published"] = pd.to_datetime(df["date_published"], errors="coerce")
            df["duration_minutes"] = df["duration"].apply(self._parse_duration)

            df_to_export = df[ConfigRefine.OUTPUT_COLUMNS.value]
            df_to_export.to_csv(self.output_document_csv_path, index=False, encoding='utf-8')

            self.logger.info("Datos refinados y exportados a CSV en '%s'.", self.output_document_csv_path)
            return df

        except Exception as e:
            self.logger.exception("Error procesando los datos del DataFrame: %s", str(e))
            return None

    def _read_json_file(self, file_path: str | None) -> list[dict]:
        if not file_path or not path.exists(file_path):
            self.logger.warning("Ruta no válida o archivo no encontrado: '%s'", file_path)
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.exception("Error al leer el archivo JSON '%s': %s", file_path, str(e))
            return []

    def _parse_duration(self, iso_duration: str) -> float | None:
        try:
            duration = isodate.parse_duration(iso_duration)
            return duration.total_seconds() / 60
        except Exception as e:
            self.logger.warning("Error parseando duración ISO '%s': %s", iso_duration, str(e))
            return None
