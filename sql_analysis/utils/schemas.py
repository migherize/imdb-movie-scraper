from pydantic import BaseModel

class TopMovieBase(BaseModel):
    id: int
    title: str
    year: int
    rating: float
    duration: int
    metascore: float
    decade: int
    rn: int

    model_config = {"from_attributes": True}


class StdRatingBase(BaseModel):
    year: int
    rating_stddev: float


class RatingNormalizadoBase(BaseModel):
    id: int
    title: str
    rating: float
    metascore: int
    abs_diff: float
    relative_diff: float


class ActorBase(BaseModel):
    movie_id: int
    title: str
    year: int
    rating: float
    duration: int
    metascore: int
    actor_name: str

    model_config = {"from_attributes": True}
