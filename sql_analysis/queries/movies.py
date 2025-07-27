from sqlalchemy.orm import Session
from sqlalchemy.sql import text

def get_top_movies_by_decade(db: Session):
    query = text("""
        -- Top 5 películas más largas por década
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
                ROW_NUMBER() OVER (
                    PARTITION BY (year / 10) * 10
                    ORDER BY duration DESC
                ) AS rn
            FROM movies
            WHERE duration IS NOT NULL
        ) AS ranked
        WHERE rn <= 5
        ORDER BY decade, duration DESC;
    """)
    return [dict(row._mapping) for row in db.execute(query).fetchall()]


def get_standard_deviation_rating(db: Session):
    query = text("""
        -- Desviación estándar del rating por año
        SELECT
            year,
            COALESCE(ROUND(STDDEV_SAMP(rating)::NUMERIC, 2), 0.00) AS rating_stddev
        FROM movies
        WHERE rating IS NOT NULL
        GROUP BY year
        ORDER BY year;
    """)
    return [dict(row._mapping) for row in db.execute(query).fetchall()]


def get_metascore_and_imdb_rating_normalizado(db: Session):
    query = text("""
        -- Diferencias significativas entre metascore e IMDb (>20%)
        SELECT
            id,
            title,
            rating,
            metascore,
            ROUND(ABS(rating - metascore / 10.0)::numeric, 2) AS abs_diff,
            ROUND((ABS(rating - metascore / 10.0) / rating)::numeric, 2) AS relative_diff
        FROM movies
        WHERE rating IS NOT NULL
          AND metascore IS NOT NULL
          AND ABS(rating - metascore / 10.0) / rating > 0.20;
    """)
    return [dict(row._mapping) for row in db.execute(query).fetchall()]

