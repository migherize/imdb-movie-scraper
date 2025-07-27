import os
import logging
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from imdb_movies.enum_model import ConfigDB
from imdb_movies.models_patterns.models import Base
from imdb_movies.models_patterns.error_handlers import ErrorHandler, ErrorType, retry_with_backoff, RetryConfig


class DatabaseStrategy(ABC):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        self.logger = logger or logging.getLogger(__name__)
        self.engine = None
        self.SessionLocal = None
        self._connection_validated = False
        self.error_handler = ErrorHandler(self.logger)

    @abstractmethod
    def get_connection_string(self) -> str:
        pass

    @abstractmethod
    def _initialize_engine_safe(self):
        pass

    def get_session(self) -> Session:
        if not self.SessionLocal:
            self._initialize_engine_safe()
        return self.SessionLocal()

    def validate_connection(self) -> bool:
        try:
            session = self.get_session()
            session.execute(text("SELECT * from movies LIMIT 1"))
            session.close()
            self._connection_validated = True
            self.logger.info("✅ Conexión validada correctamente")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error validando conexión: {e}")
            self._connection_validated = False
            return False

    def is_connection_valid(self) -> bool:
        return self._connection_validated

    def create_tables_if_not_exist(self):
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("✅ Tablas verificadas/creadas correctamente")
        except Exception as e:
            self.logger.error(f"❌ Error creando tablas: {e}")
            raise
class PostgreSQLStrategy(DatabaseStrategy):

    def __init__(self, logger=None, **kwargs):
        super().__init__(logger, **kwargs)
        self._initialize_engine_safe()

    def get_connection_string(self) -> str:
        db = ConfigDB.DB.value
        user = ConfigDB.USERDB.value
        password = ConfigDB.PASSWORDDB.value
        host = ConfigDB.NAME_SERVICEDB.value
        port = ConfigDB.PORT.value
        database = ConfigDB.NAMEDB.value

        return f"{db}://{user}:{password}@{host}:{port}/{database}"

    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=2.0),
        retry_on=(SQLAlchemyError, DisconnectionError)
    )
    def _initialize_engine_safe(self):
        connection_string = self.get_connection_string()
        engine_config = {
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'echo': False
        }
        self.engine = create_engine(connection_string, **engine_config)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger.info("🐘 Engine PostgreSQL inicializado correctamente")
class SQLiteStrategy(DatabaseStrategy):
    """Estrategia para base de datos SQLite con manejo robusto de errores"""
    
    def __init__(self, db_path: str = "imdb_movies.db", logger: logging.Logger = None):
        super().__init__(logger)
        self.db_path = self._validate_db_path(db_path)
        self._initialize_engine_safe()

    def _validate_db_path(self, db_path: str) -> str:
        """Valida y normaliza la ruta de la base de datos SQLite"""
        try:
            import os
            
            # Si es ruta relativa, hacerla absoluta
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            
            # Crear directorio padre si no existe
            parent_dir = os.path.dirname(db_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                self.logger.info(f"📁 Directorio creado para SQLite: {parent_dir}")
            
            self.logger.debug(f"💾 Ruta SQLite validada: {db_path}")
            return db_path
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.FILE_IO_ERROR, 
                f"Validando ruta SQLite: {db_path}"
            )
            # Fallback a ruta por defecto
            return "imdb_movies.db"

    def get_connection_string(self) -> str:
        """Construye la cadena de conexión para SQLite"""
        return f"sqlite:///{self.db_path}"

    def _initialize_engine_safe(self):
        """Inicializa el engine de SQLAlchemy para SQLite"""
        try:
            connection_string = self.get_connection_string()
            
            # Configuraciones específicas para SQLite
            engine_config = {
                'echo': False,
                'connect_args': {
                    'check_same_thread': False,  # Permite uso en múltiples threads
                    'timeout': 20  # Timeout en segundos
                }
            }
            
            self.engine = create_engine(connection_string, **engine_config)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            self.logger.info(f"💾 Engine SQLite inicializado: {self.db_path}")
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                f"Inicializando engine SQLite: {self.db_path}", 
                fatal=True
            )
            raise

    def get_session(self) -> Session:
        """Retorna una nueva sesión de SQLite"""
        if not self.SessionLocal:
            raise RuntimeError("Engine SQLite no inicializado")
        
        try:
            session = self.SessionLocal()
            # Configurar SQLite para mejor concurrencia
            session.execute(text("PRAGMA journal_mode=WAL"))
            session.execute(text("PRAGMA synchronous=NORMAL"))
            session.execute(text("PRAGMA cache_size=10000"))
            return session
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Creando sesión SQLite"
            )
            raise


class MySQLStrategy(DatabaseStrategy):
    """Estrategia para base de datos MySQL con manejo robusto de errores"""
    
    def __init__(self, logger: logging.Logger = None):
        super().__init__(logger)
        self._initialize_engine_safe()

    def get_connection_string(self) -> str:
        """Construye la cadena de conexión para MySQL con validación"""
        try:
            user = os.getenv("MYSQL_USER", "root")
            password = os.getenv("MYSQL_PASSWORD", "")
            host = os.getenv("MYSQL_HOST", "localhost")
            port = os.getenv("MYSQL_PORT", "3306")
            database = os.getenv("MYSQL_DATABASE", "imdb_movies")
            
            # Validar parámetros críticos
            if not user:
                raise ValueError("Usuario MySQL no especificado")
            if not database:
                raise ValueError("Base de datos MySQL no especificada")
            
            connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            
            # Log seguro
            safe_string = f"mysql+pymysql://{user}:***@{host}:{port}/{database}"
            self.logger.debug(f"🐬 Cadena de conexión MySQL: {safe_string}")
            
            return connection_string
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Construyendo cadena de conexión MySQL"
            )
            raise

    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=2.0),
        retry_on=(SQLAlchemyError,)
    )
    def _initialize_engine_safe(self):
        """Inicializa el engine de SQLAlchemy para MySQL"""
        try:
            connection_string = self.get_connection_string()
            
            # Configuraciones específicas para MySQL
            engine_config = {
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'echo': False,
                'connect_args': {
                    'charset': 'utf8mb4',
                    'connect_timeout': 10
                }
            }
            
            self.engine = create_engine(connection_string, **engine_config)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            self.logger.info("🐬 Engine MySQL inicializado exitosamente")
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Inicializando engine MySQL", 
                fatal=True
            )
            raise

    @retry_with_backoff(
        config=RetryConfig(max_retries=2, base_delay=1.0),
        retry_on=(SQLAlchemyError,)
    )
    def get_session(self) -> Session:
        """Retorna una nueva sesión de MySQL"""
        if not self.SessionLocal:
            raise RuntimeError("Engine MySQL no inicializado")
        
        try:
            session = self.SessionLocal()
            # Configurar MySQL para mejor manejo de UTF-8
            session.execute(text("SET NAMES utf8mb4"))
            session.execute(text("SET CHARACTER SET utf8mb4"))
            session.execute(text("SET character_set_connection=utf8mb4"))
            return session
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Creando sesión MySQL"
            )
            raise


class DatabaseStrategyFactory:
    _strategies = {
        'postgresql': PostgreSQLStrategy,
        'sqlite': SQLiteStrategy,
        'mysql': MySQLStrategy
    }

    @classmethod
    def create_strategy(cls, db_type: str, logger: logging.Logger = None, **kwargs) -> DatabaseStrategy:
        if db_type not in cls._strategies:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}. Disponibles: {available}")

        strategy_class = cls._strategies[db_type]
        strategy = strategy_class(logger=logger, **kwargs)

        if not strategy.validate_connection():
            raise RuntimeError(f"No se pudo validar conexión para {db_type}")

        strategy.create_tables_if_not_exist()
        if logger:
            logger.info(f"✅ Estrategia {db_type} creada y validada exitosamente")

        return strategy
