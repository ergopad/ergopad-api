from pydantic import BaseModel
import typing as t

### SCHEMAS FOR PROJECTS ###


class Socials(BaseModel):
    telegram: t.Optional[str]
    twitter: t.Optional[str]
    discord: t.Optional[str]
    github: t.Optional[str]
    website: t.Optional[str]


class CreateAndUpdateProject(BaseModel):
    name: str
    shortDescription: str
    description: t.Optional[str]
    fundsRaised: t.Optional[float]
    socials: Socials
    bannerImgUrl: str
    isLaunched: bool


class Project(CreateAndUpdateProject):
    id: int

    class Config:
        orm_mode = True


class CreateAndUpdateProjectTeamMember(BaseModel):
    name: str
    description: t.Optional[str]
    # we do not know projectId when project is created
    projectId: t.Optional[int]
    profileImgUrl: t.Optional[str]


class ProjectTeamMember(CreateAndUpdateProjectTeamMember):
    id: int

    class Config:
        orm_mode = True


class ProjectWithTeam(Project):
    team: t.List[ProjectTeamMember]

    class Config:
        orm_mode = True


class CreateAndUpdateProjectWithTeam(CreateAndUpdateProject):
    team: t.Optional[t.List[CreateAndUpdateProjectTeamMember]]
