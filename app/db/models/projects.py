from sqlalchemy import JSON, Boolean, Column, Integer, String, Float

from db.session import Base

# PROJECTS MODEL


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    fundsRaised = Column(Float)
    shortDescription = Column(String)
    description = Column(String)
    bannerImgUrl = Column(String)
    isLaunched = Column(Boolean)
    socials = Column(JSON)
    roadmap = Column(JSON)
    team = Column(JSON)
    tokenomics = Column(JSON)
