"""
Definición del objeto base para los modelos de SQLAlchemy en imdb_scraper.

Todos los modelos ORM deben heredar de esta clase `Base`.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
