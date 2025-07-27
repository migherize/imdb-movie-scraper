from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sql_analysis.db.database import get_db
from sql_analysis.utils.schemas import TopMovieBase, StdRatingBase, RatingNormalizadoBase, ActorBase
from sql_analysis.queries.movies import get_top_movies_by_decade, get_standard_deviation_rating,get_metascore_and_imdb_rating_normalizado
from sql_analysis.queries.actor import create_view_actor_movie, get_view_actor_movie

router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)

@router.get("/top-by-decade", response_model=List[TopMovieBase])
def fetch_top_movies_by_decade(db: Session = Depends(get_db)):
    """
    Devuelve las 5 películas con mayor promedio de duración por década.
    """
    return get_top_movies_by_decade(db)

@router.get("/ratings/std-dev", response_model=List[StdRatingBase])
def fetch_ratings_std_deviation(db: Session = Depends(get_db)):
    """
    Calcula la desviación estándar de las calificaciones por año.
    """
    return get_standard_deviation_rating(db)

@router.get("/ratings/diff", response_model=List[RatingNormalizadoBase])
def fetch_rating_differences(db: Session = Depends(get_db)):
    """
    Detecta películas con más de un 20% de diferencia entre IMDB y Metascore.
    """
    return get_metascore_and_imdb_rating_normalizado(db)

@router.get("/actors/view", response_model=List[ActorBase])
def fetch_movies_actors_view(
    actor_name: Optional[str] = Query(None, description="Nombre del actor principal"),
    db: Session = Depends(get_db)
):
    """
    Devuelve una vista que relaciona películas y actores.
    Se puede filtrar por el nombre del actor.
    """

    create_view_actor_movie(db)
    return get_view_actor_movie(db, actor_name)
