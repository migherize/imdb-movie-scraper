import os
import pytest
from sqlalchemy import text
from sql_analysis.db.database import SessionLocal

REQUIRED_ENV_VARS = [
    "PYTHONPATH",
    "DB",
    "NAMEDB",
    "USERDB",
    "PASSWORDDB",
    "PORT",
    "NAME_SERVICEDB",
]


def test_environment_variables():
    """
    Verifica que las variables de entorno necesarias estén configuradas.
    """
    for var in REQUIRED_ENV_VARS:
        assert os.getenv(var), f"Falta la variable de entorno: {var}"


def test_database_connection():
    """
    Intenta conectarse a la base de datos y ejecutar una query simple.
    """
    try:
        db = SessionLocal()
        print(  db.execute(text("SELECT * from movies LIMIT 1")))
        db.execute(text("SELECT * from movies LIMIT 1"))
    except Exception as e:
        pytest.fail(f"No se pudo conectar a la base de datos: {e}")
    finally:
        db.close()


def test_database_has_data():
    """
    Verifica si la base de datos contiene datos en la tabla movies.
    """
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT COUNT(*) FROM movies"))
        count = result.scalar()
        assert (
            count > 0
        ), "La tabla 'movies' está vacía. Carga los datos antes de continuar."
    finally:
        db.close()
