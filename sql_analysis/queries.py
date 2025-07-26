from sqlalchemy.orm import Session
from sqlalchemy.sql import text

def get_top_movies_by_decade(db: Session):
    query = text("""
        SELECT *
        FROM (
            SELECT 
                id,
                title,
                year,
                rating,
                metascore,
                duration,
                (year / 10) * 10 AS decade,
                ROW_NUMBER() OVER (PARTITION BY (year / 10) * 10 ORDER BY duration DESC) AS rn
            FROM movies
            WHERE duration IS NOT NULL
        ) AS sub
        WHERE rn <= 5
        ORDER BY decade, duration DESC;
    """)
    return db.execute(query).fetchall()

