from sqlalchemy import Column, Integer, String, JSON
from db.session import Base


class Tutorial(Base):
    __tablename__ = "tutorials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    shortDescription = Column(String)
    description = Column(String)
    link = Column(String)
    linkType = Column(String)
    bannerImgUrl = Column(String)
    category = Column(String)
    config = Column(JSON)
