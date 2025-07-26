from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from sql_analysis.db.database import get_db
from sql_analysis.queries import get_top_movies_by_decade
from sql_analysis.schemas import MovieBase

router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)

@router.get("/top-by-decade", response_model=List[MovieBase])
def top_movies_by_decade(db: Session = Depends(get_db)):
    """
    Devuelve las mejores películas por década según el rating.
    """
    return get_top_movies_by_decade(db)
