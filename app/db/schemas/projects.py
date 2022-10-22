from datetime import datetime
from pydantic import BaseModel
import typing as t

### SCHEMAS FOR PROJECTS ###


class Socials(BaseModel):
    telegram: t.Optional[str]
    twitter: t.Optional[str]
    discord: t.Optional[str]
    github: t.Optional[str]
    website: t.Optional[str]
    linkedin: t.Optional[str]


class Tokenomics(BaseModel):
    name: str
    amount: float
    value: t.Optional[str]
    tge: t.Optional[str]
    freq: t.Optional[str]
    length: t.Optional[str]
    lockup: t.Optional[str]


class TokenomicsJSONList(BaseModel):
    tokenName: t.Optional[str]
    totalTokens: t.Optional[float]
    tokenTicker: t.Optional[str]
    tokenomics: t.List[Tokenomics]


class TeamMember(BaseModel):
    name: str
    description: t.Optional[str]
    profileImgUrl: t.Optional[str]
    socials: Socials


class TeamMemberJSONList(BaseModel):
    team: t.List[TeamMember]


class Roadmap(BaseModel):
    name: str
    description: t.Optional[str]
    date: str


class RoadmapJSONList(BaseModel):
    roadmap: t.List[Roadmap]


class CreateAndUpdateProject(BaseModel):
    name: str
    shortDescription: str
    description: t.Optional[str]
    fundsRaised: t.Optional[float]
    bannerImgUrl: str
    isLaunched: bool
    socials: Socials
    roadmap: RoadmapJSONList
    team: TeamMemberJSONList
    tokenomics: TokenomicsJSONList
    isDraft: bool = False


class Project(CreateAndUpdateProject):
    id: int

    class Config:
        orm_mode = True
