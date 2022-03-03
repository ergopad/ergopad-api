from pydantic import BaseModel
import datetime
import typing as t


class CreateAndUpdateAnnouncement(BaseModel):
    title: str
    shortDescription: str
    description: t.Optional[str]
    bannerImgUrl: str
    tag: t.Optional[str]


class Announcement(CreateAndUpdateAnnouncement):
    createdTimestamp: datetime.datetime
    id: int

    class Config:
        orm_mode = True
