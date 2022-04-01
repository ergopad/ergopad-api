from datetime import datetime
from pydantic import BaseModel
import typing as t


class CheckBoxes(BaseModel):
    checkBoxText: t.List[str]


class CreateWhitelistEvent(BaseModel):
    projectName: str
    roundName: str
    title: str
    subtitle: str
    details: str
    checkBoxes: CheckBoxes
    additionalDetails: dict
    total_sigusd: float
    buffer_sigusd: float
    individualCap: int
    start_dtz: datetime
    end_dtz: datetime


class WhitelistEvent(CreateWhitelistEvent):
    id: int
    eventId: int
    eventName: str

    class Config:
        orm_mode = True
