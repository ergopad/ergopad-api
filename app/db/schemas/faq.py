from pydantic import BaseModel
import typing as t


class CreateAndUpdateFaq(BaseModel):
    question: str
    solution: t.Optional[str]
    tag: t.Optional[str]


class Faq(CreateAndUpdateFaq):
    id: int

    class Config:
        orm_mode = True
