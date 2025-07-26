from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sql_analysis.db.base import Base

class Movie(Base):
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    year = Column(Integer)
    rating = Column(Float)
    duration = Column(Integer)
    metascore = Column(Float)

    actors = relationship("Actor", back_populates="movie")


class Actor(Base):
    __tablename__ = 'actors'

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'))
    name = Column(String)

    movie = relationship("Movie", back_populates="actors")
