from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from db.session import Base

# ANNOUNCEMENT MODEL


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    createdTimestamp = Column(DateTime(timezone=True),
                              server_default=func.now())
    title = Column(String)
    shortDescription = Column(String)
    description = Column(String)
    bannerImgUrl = Column(String)
    tag = Column(String)
