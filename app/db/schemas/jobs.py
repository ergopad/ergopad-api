from pydantic import BaseModel
import typing as t


class CreateAndUpdateJob(BaseModel):
    title: str
    shortDescription: str
    description: t.Optional[str]
    category: str
    archived: bool


class Job(CreateAndUpdateJob):
    id: int

    class Config:
        orm_mode = True
