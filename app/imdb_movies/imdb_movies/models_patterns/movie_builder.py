from typing import Optional, List
from imdb_movies.models import Movie, Actor
import ast


class MovieBuilder:
    """Builder Pattern para construir objetos Movie de forma flexible"""
    
    def __init__(self):
        self.reset()

    def reset(self):
        """Reinicia el builder para construir un nuevo objeto Movie"""
        self._movie = Movie()
        self._actors_data = []
        return self
    
    def set_title(self, title: str):
        """Establece el título de la película"""
        self._movie.title = title
        return self
    
    def set_year(self, year: Optional[int]):
        """Establece el año de la película"""
        if year is not None:
            self._movie.year = int(year)
        return self
    
    def set_year_from_date(self, date_published: str):
        """Establece el año extrayéndolo de la fecha de publicación"""
        if date_published:
            try:
                year = int(str(date_published)[:4])
                self._movie.year = year
            except (ValueError, TypeError):
                pass
        return self
    
    def set_rating(self, rating: Optional[float]):
        """Establece el rating de la película"""
        if rating is not None:
            try:
                self._movie.rating = float(rating)
            except (ValueError, TypeError):
                pass
        return self
    
    def set_duration(self, duration_minutes: Optional[float]):
        """Establece la duración de la película en minutos"""
        if duration_minutes is not None:
            try:
                self._movie.duration = int(duration_minutes)
            except (ValueError, TypeError):
                pass
        return self
    
    def set_metascore(self, metascore: Optional[float]):
        """Establece el metascore de la película"""
        if metascore is not None:
            try:
                self._movie.metascore = float(metascore)
            except (ValueError, TypeError):
                pass
        return self
    
    def set_actors_from_raw_data(self, actors_raw):
        """Establece los actores procesando datos en diferentes formatos"""
        actor_names = []
        
        if actors_raw:
            if isinstance(actors_raw, list):
                actor_names = actors_raw
            elif isinstance(actors_raw, str):
                try:
                    # Intentar evaluar como lista literal
                    actor_names = ast.literal_eval(actors_raw)
                    if not isinstance(actor_names, list):
                        raise ValueError
                except Exception:
                    # Si falla, dividir por punto y coma
                    actor_names = [a.strip() for a in actors_raw.split(';')]
        
        self._actors_data = actor_names
        return self
    
    def add_actor(self, actor_name: str):
        """Añade un actor individual"""
        if actor_name and actor_name.strip():
            self._actors_data.append(actor_name.strip())
        return self
    
    def build(self) -> Movie:
        """Construye y retorna el objeto Movie final"""
        movie = self._movie
        
        # Crear objetos Actor y asociarlos
        actors = []
        for actor_name in self._actors_data:
            if actor_name:  # Solo crear actores con nombres válidos
                actor = Actor(name=actor_name)
                actors.append(actor)
        
        movie.actors = actors
        
        # Resetear para el siguiente uso
        result = movie
        self.reset()
        return result
    
    def build_from_row(self, row) -> Movie:
        """Construye un Movie completo a partir de una fila de datos"""
        return (self
                .set_title(row.get('title', ''))
                .set_year_from_date(row.get('date_published', ''))
                .set_rating(row.get('rating'))
                .set_duration(row.get('duration_minutes'))
                .set_metascore(row.get('metascore'))
                .set_actors_from_raw_data(row.get('actors', []))
                .build())


class MovieBuilderFactory:
    """Factory para crear diferentes tipos de builders de Movie"""
    
    @staticmethod
    def create_builder() -> MovieBuilder:
        """Crear un builder estándar para Movie"""
        return MovieBuilder()
    
    @staticmethod
    def create_simple_builder() -> 'SimpleMovieBuilder':
        """Crear un builder simplificado para casos básicos"""
        return SimpleMovieBuilder()


class SimpleMovieBuilder(MovieBuilder):
    """Builder simplificado para casos básicos donde solo se necesitan datos esenciales"""
    
    def build_simple(self, title: str, year: int = None, rating: float = None) -> Movie:
        """Construye un Movie con solo los datos esenciales"""
        return (self
                .set_title(title)
                .set_year(year)
                .set_rating(rating)
                .build()) 