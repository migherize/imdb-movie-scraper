from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from imdb_movies.enum_model import ConfigDB
from imdb_movies.error_handlers import ErrorHandler, ErrorType, retry_with_backoff, RetryConfig
import os
import logging
from typing import Optional


class DatabaseStrategy(ABC):
    """Interfaz abstracta para estrategias de base de datos - Strategy Pattern con manejo de errores"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.engine = None
        self.SessionLocal = None
        self._connection_validated = False
    
    @abstractmethod
    def get_connection_string(self) -> str:
        """Retorna la cadena de conexión a la base de datos"""
        pass
    
    @abstractmethod
    def get_session(self) -> Session:
        """Retorna una sesión de base de datos"""
        pass
    
    def validate_connection(self) -> bool:
        """Valida la conexión a la base de datos"""
        try:
            test_session = self.get_session()
            test_session.execute(text("SELECT 1"))
            test_session.close()
            self._connection_validated = True
            self.logger.info("✅ Conexión a base de datos validada exitosamente")
            return True
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Validando conexión a base de datos"
            )
            self._connection_validated = False
            return False
    
    def is_connection_valid(self) -> bool:
        """Retorna si la conexión fue validada"""
        return self._connection_validated
    
    def create_tables_if_not_exist(self):
        """Crea las tablas si no existen"""
        try:
            from imdb_movies.models import Base
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("✅ Tablas de base de datos verificadas/creadas")
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Creando tablas de base de datos"
            )


class PostgreSQLStrategy(DatabaseStrategy):
    """Estrategia para base de datos PostgreSQL con manejo robusto de errores"""
    
    def __init__(self, logger: logging.Logger = None):
        super().__init__(logger)
        self._initialize_engine_safe()

    def get_connection_string(self) -> str:
        """Construye la cadena de conexión para PostgreSQL con validación"""
        try:
            db = ConfigDB.DB.value
            user = ConfigDB.USERDB.value
            password = ConfigDB.PASSWORDDB.value
            host = ConfigDB.NAME_SERVICEDB.value
            port = ConfigDB.PORT.value
            database = ConfigDB.NAMEDB.value
            
            # Validar parámetros requeridos
            required_params = {
                'db': db, 'user': user, 'password': password,
                'host': host, 'port': port, 'database': database
            }
            
            missing_params = [k for k, v in required_params.items() if not v]
            if missing_params:
                raise ValueError(f"Parámetros de conexión PostgreSQL faltantes: {missing_params}")
            
            connection_string = f"{db}://{user}:{password}@{host}:{port}/{database}"
            
            # Log de conexión (sin mostrar password)
            safe_string = f"{db}://{user}:***@{host}:{port}/{database}"
            self.logger.debug(f"🔗 Cadena de conexión PostgreSQL: {safe_string}")
            
            return connection_string
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Construyendo cadena de conexión PostgreSQL"
            )
            raise

    @retry_with_backoff(
        config=RetryConfig(max_retries=3, base_delay=2.0),
        retry_on=(SQLAlchemyError, DisconnectionError)
    )
    def _initialize_engine_safe(self):
        """Inicializa el engine de SQLAlchemy de forma segura"""
        try:
            connection_string = self.get_connection_string()
            
            # Configuraciones adicionales para PostgreSQL
            engine_config = {
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'echo': False  # Cambiar a True para debug SQL
            }
            
            self.engine = create_engine(connection_string, **engine_config)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            self.logger.info("🐘 Engine PostgreSQL inicializado exitosamente")
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Inicializando engine PostgreSQL", 
                fatal=True
            )
            raise

    @retry_with_backoff(
        config=RetryConfig(max_retries=2, base_delay=1.0),
        retry_on=(SQLAlchemyError,)
    )
    def get_session(self) -> Session:
        """Retorna una nueva sesión de PostgreSQL con validación"""
        if not self.SessionLocal:
            raise RuntimeError("Engine PostgreSQL no inicializado")
        
        try:
            session = self.SessionLocal()
            # Validar sesión con query simple
            session.execute(text("SELECT version()"))
            return session
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorType.DATABASE_ERROR, 
                "Creando sesión PostgreSQL"
            )
            raise


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
    """Factory mejorado para crear estrategias de base de datos con validación"""
    
    _strategies = {
        'postgresql': PostgreSQLStrategy,
        'sqlite': SQLiteStrategy,
        'mysql': MySQLStrategy
    }
    
    @classmethod
    def create_strategy(cls, db_type: str, logger: logging.Logger = None, **kwargs) -> DatabaseStrategy:
        """Crea una estrategia de base de datos con validación mejorada"""
        if db_type not in cls._strategies:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}. Disponibles: {available}")
        
        strategy_class = cls._strategies[db_type]
        
        try:
            # Crear estrategia con parámetros específicos
            if db_type == 'sqlite':
                db_path = kwargs.get('db_path', 'imdb_movies.db')
                strategy = strategy_class(db_path, logger)
            else:
                strategy = strategy_class(logger)
            
            # Validar conexión
            if not strategy.validate_connection():
                raise RuntimeError(f"No se pudo validar conexión para {db_type}")
            
            # Crear tablas si no existen
            strategy.create_tables_if_not_exist()
            
            if logger:
                logger.info(f"✅ Estrategia {db_type} creada y validada exitosamente")
            
            return strategy
            
        except Exception as e:
            if logger:
                logger.error(f"❌ Error creando estrategia {db_type}: {e}")
            raise
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """Retorna la lista de estrategias de base de datos disponibles"""
        return list(cls._strategies.keys())
    
    @classmethod
    def create_default_strategy(cls, logger: logging.Logger = None) -> DatabaseStrategy:
        """Crea la estrategia de base de datos por defecto con fallback inteligente"""
        db_type = getattr(ConfigDB.DB, 'value', None)
        
        # Intentar determinar tipo de BD desde configuración
        if db_type and 'postgresql' in db_type.lower():
            return cls._try_create_with_fallback('postgresql', logger)
        elif db_type and 'sqlite' in db_type.lower():
            return cls._try_create_with_fallback('sqlite', logger)
        elif db_type and 'mysql' in db_type.lower():
            return cls._try_create_with_fallback('mysql', logger)
        else:
            # Fallback inteligente: PostgreSQL -> SQLite
            return cls._try_create_with_fallback('postgresql', logger, fallback='sqlite')
    
    @classmethod
    def _try_create_with_fallback(cls, 
                                  primary: str, 
                                  logger: logging.Logger = None, 
                                  fallback: str = 'sqlite') -> DatabaseStrategy:
        """Intenta crear estrategia primaria, si falla usa fallback"""
        try:
            return cls.create_strategy(primary, logger)
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Estrategia {primary} falló: {e}")
            
            if fallback and fallback != primary:
                try:
                    if logger:
                        logger.info(f"🔄 Intentando fallback a {fallback}")
                    return cls.create_strategy(fallback, logger)
                except Exception as fallback_error:
                    if logger:
                        logger.error(f"❌ Fallback {fallback} también falló: {fallback_error}")
                    raise fallback_error
            else:
                raise e
    
    @classmethod
    def test_all_strategies(cls, logger: logging.Logger = None) -> dict:
        """Prueba todas las estrategias disponibles y retorna su estado"""
        results = {}
        
        for strategy_name in cls._strategies.keys():
            try:
                strategy = cls.create_strategy(strategy_name, logger)
                results[strategy_name] = {
                    'status': 'success',
                    'connection_valid': strategy.is_connection_valid(),
                    'message': 'Estrategia creada y validada exitosamente'
                }
            except Exception as e:
                results[strategy_name] = {
                    'status': 'failed',
                    'connection_valid': False,
                    'message': str(e)
                }
        
        return results 