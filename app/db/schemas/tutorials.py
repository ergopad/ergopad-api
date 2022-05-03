from pydantic import BaseModel
import typing as t


class CreateAndUpdateTutorial(BaseModel):
    title: str
    shortDescription: t.Optional[str]
    description: t.Optional[str]
    link: t.Optional[str]
    linkType: t.Optional[str]
    bannerImgUrl: t.Optional[str]
    category: t.Optional[str]
    config: dict


class Tutorial(CreateAndUpdateTutorial):
    id: int

    class Config:
        orm_mode = True
