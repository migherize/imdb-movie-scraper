from imdb_movies.models_patterns.models import Movie, Actor
import ast
from typing import List

class MovieFactory:
    @staticmethod
    def create_movie_from_row(row: dict) -> Movie:
        title = row.get('title')
        year = int(str(row['date_published'])[:4]) if row.get('date_published') else None
        rating = float(row['rating']) if row.get('rating') else None
        duration = int(row['duration_minutes']) if row.get('duration_minutes') else None
        metascore = float(row['metascore']) if row.get('metascore') else None
        actors_raw = row.get('actors')

        movie = Movie(
            title=title,
            year=year,
            rating=rating,
            duration=duration,
            metascore=metascore
        )

        actor_names: List[str] = []
        if actors_raw:
            if isinstance(actors_raw, list):
                actor_names = actors_raw
            elif isinstance(actors_raw, str):
                try:
                    actor_names = ast.literal_eval(actors_raw)
                    if not isinstance(actor_names, list):
                        raise ValueError
                except Exception:
                    actor_names = [a.strip() for a in actors_raw.split(';')]

        movie.actors = [Actor(name=a) for a in actor_names if a]
        return movie
