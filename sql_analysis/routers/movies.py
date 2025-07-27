from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from sql_analysis.db.database import get_db
from sql_analysis.models.schemas import TopMovieBase, StdRatingBase, RatingNormalizadoBase, ActorBase
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
    try:
        return get_top_movies_by_decade(db)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de la db: {str(e)}")


@router.get("/ratings/std-dev", response_model=List[StdRatingBase])
def fetch_ratings_std_deviation(db: Session = Depends(get_db)):
    """
    Calcula la desviación estándar de las calificaciones por año.
    """
    try:
        return get_standard_deviation_rating(db)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de la db: {str(e)}")

@router.get("/ratings/diff", response_model=List[RatingNormalizadoBase])
def fetch_rating_differences(db: Session = Depends(get_db)):
    """
    Detecta películas con más de un 20% de diferencia entre IMDB y Metascore.
    """
    try:
        return get_metascore_and_imdb_rating_normalizado(db)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de la db: {str(e)}")

@router.get("/actors/view", response_model=List[ActorBase])
def fetch_movies_actors_view(
    actor_name: Optional[str] = Query(None, description="Nombre del actor principal"),
    db: Session = Depends(get_db)
):
    """
    Devuelve una vista que relaciona películas y actores.
    Se puede filtrar por el nombre del actor.
    """

    try:
        create_view_actor_movie(db)
        return get_view_actor_movie(db, actor_name)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de la vista: {str(e)}")
