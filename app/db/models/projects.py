from sqlalchemy import Boolean, Column, Integer, String, Float

from db.session import Base

# PROJECTS MODEL


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    fundsRaised = Column(Float)
    shortDescription = Column(String)
    description = Column(String)
    socials = Column(String)
    bannerImgUrl = Column(String)
    isLaunched = Column(Boolean)


class ProjectTeam(Base):
    __tablename__ = "projectTeams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    profileImgUrl = Column(String)
    projectId = Column(Integer)
