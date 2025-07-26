from pydantic import BaseModel
from typing import List, Optional

class MovieBase(BaseModel):
    id: int
    title: str
    year: int
    duration: int

    model_config = {"from_attributes": True}



class ActorBase(BaseModel):
    id: int
    name: str
    movie_id: int

    model_config = {"from_attributes": True}



class MovieWithActors(MovieBase):
    actors: List[ActorBase]
