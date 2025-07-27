from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import Optional



def create_view_actor_movie(db: Session):
    query = text("""
        -- Vista que une películas y actores
        CREATE OR REPLACE VIEW movie_actor_view AS
        SELECT
            m.id AS movie_id,
            m.title,
            m.year,
            m.rating,
            m.duration,
            m.metascore,
            a.name AS actor_name
        FROM movies m
        JOIN actors a ON m.id = a.movie_id;
    """)
    db.execute(query)
    db.commit()

def get_view_actor_movie(db: Session, actor_name: Optional[str] = None):
    if actor_name:
        query = text(
            """
            SELECT *
            FROM movie_actor_view
            WHERE actor_name = :actor_name
            """
        )
        result = db.execute(query, {"actor_name": actor_name})
    else:
        query = text("SELECT * FROM movie_actor_view")
        result = db.execute(query)

    return [dict(row._mapping) for row in result.fetchall()]
