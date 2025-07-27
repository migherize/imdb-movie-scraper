import json
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from imdb_movies.models import Movie, Actor
from imdb_movies.enum_model import ConfigDB
from imdb_movies.error_handlers import (
    ErrorHandler, ErrorType, DataValidator, 
    retry_with_backoff, RetryConfig, SafeOperations
)
import ast
import logging
from sqlalchemy import text


class DataExporter(ABC):
    """Interfaz abstracta para exportadores de datos - Strategy Pattern"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
    
    @abstractmethod
    def export(self, data: List[Dict[str, Any]], output_path: str, logger=None) -> bool:
        """Exporta los datos al formato correspondiente"""
        pass
    
    def validate_data_batch(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida un lote de datos antes de exportar"""
        validated_data = []
        
        for i, item in enumerate(data):
            try:
                # Extraer info_movie si existe
                movie_info = item.get('info_movie', item)
                
                # Validar datos
                validated_movie = DataValidator.validate_movie_data(movie_info, self.logger)
                validated_data.append({'info_movie': validated_movie})
                
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorType.DATA_VALIDATION_ERROR, 
                    f"Validando item {i}", movie_info
                )
                # Continuar con el siguiente item
                continue
        
        self.logger.info(f"✅ Validados {len(validated_data)}/{len(data)} items exitosamente")
        return validated_data


class JSONExporter(DataExporter):
    """Exportador de datos en formato JSON con manejo robusto de errores"""
    
    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=1.0),
        retry_on=(OSError, IOError)
    )
    def export(self, data: List[Dict[str, Any]], output_path: str, logger=None) -> bool:
        """Exporta datos a JSON con validación y manejo de errores"""
        active_logger = logger or self.logger
        
        try:
            # Validar datos antes de exportar
            validated_data = self.validate_data_batch(data)
            
            if not validated_data:
                active_logger.warning("⚠️ No hay datos válidos para exportar a JSON")
                return False
            
            # Usar operación segura de escritura
            success = SafeOperations.safe_file_write(
                output_path, validated_data, logger=active_logger
            )
            
            if success:
                active_logger.info(f"✅ {len(validated_data)} items exportados exitosamente a JSON: {output_path}")
                return True
            else:
                self.error_handler.handle_error(
                    Exception("Fallo en escritura segura"), 
                    ErrorType.FILE_IO_ERROR, 
                    "Exportando JSON"
                )
                return False
                
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.FILE_IO_ERROR, 
                f"Exportando JSON a {output_path}"
            )
            return False


class CSVExporter(DataExporter):
    """Exportador de datos en formato CSV con transformaciones robustas"""
    
    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=2.0),
        retry_on=(Exception,)
    )
    def export(self, data: List[Dict[str, Any]], output_path: str, logger=None) -> bool:
        """Exporta datos a CSV con validación y transformaciones"""
        active_logger = logger or self.logger
        
        try:
            # Validar datos
            validated_data = self.validate_data_batch(data)
            
            if not validated_data:
                active_logger.warning("⚠️ No hay datos válidos para exportar a CSV")
                return False
            
            # Convertir a DataFrame
            input_to_dataframe = [movie.get('info_movie', {}) for movie in validated_data]
            df = pd.DataFrame(input_to_dataframe)
            
            if df.empty:
                active_logger.warning("⚠️ DataFrame vacío, no se puede exportar CSV")
                return False
            
            # Aplicar transformaciones seguras
            print("entra de _apply_safe_transformations", df)
            df = self._apply_safe_transformations(df, active_logger)
            
            # Definir columnas de salida
            output_columns = [
                "title", "date_published", "rating", 
                "duration_minutes", "metascore", "actors", "movie_url"
            ]
            
            # Filtrar solo columnas existentes
            available_columns = [col for col in output_columns if col in df.columns]
            
            if not available_columns:
                active_logger.error("❌ No hay columnas válidas para exportar")
                return False
            
            # Exportar CSV de forma segura
            try:
                import os
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df[available_columns].to_csv(output_path, index=False, encoding='utf-8')
                
                active_logger.info(f"✅ {len(df)} filas exportadas exitosamente a CSV: {output_path}")
                return True
                
            except Exception as csv_error:
                self.error_handler.handle_error(
                    csv_error, ErrorType.FILE_IO_ERROR, 
                    f"Escribiendo CSV a {output_path}"
                )
                return False
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.UNKNOWN_ERROR, 
                f"Exportando CSV general"
            )
            return False
    
    def _apply_safe_transformations(self, df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
        """Aplica transformaciones de forma segura con manejo de errores"""
        # try:
        from imdb_movies.enum_model import ConfigRefine
        
        df = df.astype(ConfigRefine.DATA_TYPE.value)
        print("172 df", df)
        if "date_published" in df.columns:
            try:
                df["date_published"] = pd.to_datetime(df["date_published"], errors="coerce")
            except Exception as e:
                logger.warning(f"⚠️ Error procesando fechas: {e}")
        print("178 df", df)
        
        if "duration" in df.columns:
            # df["duration_minutes"] = df["duration"].apply(
            #     lambda x: self._safe_parse_duration(x, logger)
            # )
            df["duration_minutes"] = df["duration"].apply(self._parse_duration)
        print("184 df", df)
        
        return df
            
        # except Exception as e:
        #     logger.error(f"❌ Error en transformaciones: {e}")
        #     return df  # Retornar DataFrame original si fallan las transformaciones
    
    def _safe_parse_duration(self, duration_str: str, logger: logging.Logger) -> Optional[float]:
        """Parsea duración de forma segura"""
        if not duration_str:
            return None
            
        try:
            import isodate
            duration = isodate.parse_duration(duration_str)
            minutes = duration.total_seconds() / 60
            return round(minutes, 2) if minutes > 0 else None
        except Exception as e:
            logger.debug(f"⚠️ Error parseando duración '{duration_str}': {e}")
            return None
    
    def _parse_duration(self, date: str) -> None | float:
        try:
            import isodate
            duration = isodate.parse_duration(date)
            return duration.total_seconds() / 60
        except Exception as error:
            self.logger.warning(
                'Error al momento de parsear la fecha: %s. Error: %s', 
                [date], 
                error
            )
            return None


class DatabaseExporter(DataExporter):
    """Exportador de datos a base de datos con transacciones seguras"""
    
    def __init__(self, database_strategy, logger: logging.Logger = None):
        super().__init__(logger)
        self.database_strategy = database_strategy
        self.retry_config = RetryConfig(max_retries=3, base_delay=5.0)
    
    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=5.0),
        retry_on=(Exception,)
    )
    def export(self, data: List[Dict[str, Any]], output_path: str = None, logger=None) -> bool:
        """Exporta datos a base de datos con transacciones seguras"""
        active_logger = logger or self.logger
        session = None
        
        # try:
        # Validar datos
        validated_data = self.validate_data_batch(data)
        
        if not validated_data:
            active_logger.warning("⚠️ No hay datos válidos para exportar a BD")
            return False
        
        # Obtener sesión de base de datos
        session = self._get_safe_session(active_logger)
        if not session:
            return False
        
        # Procesar datos para DataFrame
        input_to_dataframe = [movie.get('info_movie', {}) for movie in validated_data]
        df = pd.DataFrame(input_to_dataframe)
        
        if df.empty:
            active_logger.warning("⚠️ DataFrame vacío para base de datos")
            return False
        
        df = CSVExporter()._apply_safe_transformations(df, active_logger)
        
        # Procesar filas en lotes
        batch_size = 50
        total_rows = len(df)
        successful_inserts = 0
        
        active_logger.info(f"📊 Procesando {total_rows} filas en lotes de {batch_size}")
        
        for i in range(0, total_rows, batch_size):
            batch_df = df.iloc[i:i + batch_size]
            batch_success = self._process_batch(batch_df, session, active_logger)
            
            if batch_success:
                successful_inserts += len(batch_df)
                active_logger.info(f"✅ Lote {i//batch_size + 1} procesado exitosamente ({len(batch_df)} filas)")
            else:
                active_logger.warning(f"⚠️ Fallos en lote {i//batch_size + 1}")
        
        # Confirmar transacción
        session.commit()
        
        active_logger.info(f'✅ {successful_inserts}/{total_rows} películas guardadas en base de datos')
        return successful_inserts > 0
        
        # except Exception as error:
        #     if session:
        #         try:
        #             session.rollback()
        #             active_logger.warning("🔄 Transacción revertida debido a error")
        #         except:
        #             pass
            
        #     self.error_handler.handle_error(
        #         error, ErrorType.DATABASE_ERROR, 
        #         "Exportación general a base de datos"
        #     )
        #     return False
            
        # finally:
        #     if session:
        #         try:
        #             session.close()
        #         except:
        #             pass
    
    def _get_safe_session(self, logger: logging.Logger) -> Optional[Session]:
        """Obtiene sesión de base de datos de forma segura"""
        try:
            session = self.database_strategy.get_session()
            # Probar conexión
            session.execute(text("SELECT * from movies LIMIT 1"))
            return session
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Obteniendo sesión de base de datos"
            )
            return None
    
    def _process_batch(self, batch_df: pd.DataFrame, session: Session, logger: logging.Logger) -> bool:
        """Procesa un lote de filas de forma segura"""
        try:
            for _, row in batch_df.iterrows():
                try:
                    movie = self._build_movie_from_row(row)
                    if movie and movie.title:  # Solo agregar si tiene título válido
                        session.add(movie)
                except Exception as row_error:
                    logger.warning(f"⚠️ Error procesando fila: {row_error}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error procesando lote: {e}")
            return False
    
    def _build_movie_from_row(self, row) -> Optional[Movie]:
        """Construye Movie usando MovieBuilder Pattern con validación"""
        try:
            from imdb_movies.movie_builder import MovieBuilderFactory
            
            builder = MovieBuilderFactory.create_builder()
            movie = builder.build_from_row(row)
            
            # Validación adicional
            if not movie.title or not movie.title.strip():
                return None
            
            return movie
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error construyendo Movie: {e}")
            return None


class DataExporterFactory:
    """Factory mejorado para crear exportadores con configuración robusta"""
    
    _exporters = {
        'json': JSONExporter,
        'csv': CSVExporter,
        'database': DatabaseExporter
    }
    
    @classmethod
    def create_exporter(cls, exporter_type: str, logger: logging.Logger = None, **kwargs) -> DataExporter:
        """Crea un exportador con manejo de errores mejorado"""
        if exporter_type not in cls._exporters:
            raise ValueError(f"Tipo de exportador no soportado: {exporter_type}")
        
        exporter_class = cls._exporters[exporter_type]
        
        try:
            if exporter_type == 'database':
                database_strategy = kwargs.get('database_strategy')
                if not database_strategy:
                    from imdb_movies.database_strategies import DatabaseStrategyFactory
                    database_strategy = DatabaseStrategyFactory.create_default_strategy()
                return exporter_class(database_strategy, logger)
            else:
                return exporter_class(logger)
                
        except Exception as e:
            if logger:
                logger.error(f"❌ Error creando exportador {exporter_type}: {e}")
            raise
    
    @classmethod
    def get_available_exporters(cls) -> List[str]:
        """Retorna la lista de exportadores disponibles"""
        return list(cls._exporters.keys())
    
    @classmethod
    def create_all_exporters(cls, logger: logging.Logger = None, **kwargs) -> Dict[str, DataExporter]:
        """Crea todos los exportadores disponibles"""
        exporters = {}
        
        for exporter_type in cls._exporters.keys():
            try:
                exporters[exporter_type] = cls.create_exporter(exporter_type, logger, **kwargs)
                if logger:
                    logger.info(f"✅ Exportador {exporter_type} creado exitosamente")
            except Exception as e:
                if logger:
                    logger.error(f"❌ Error creando exportador {exporter_type}: {e}")
                continue
        
        return exporters 