from sqlalchemy import DateTime, Column, Integer, String, Float, Sequence

from db.session import Base

# EVENTS MODEL


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    total_sigusd = Column(Float)
    buffer_sigusd = Column(Float)
    individualCap = Column(Integer)
    isWhitelist = Column(Integer)
    start_dtz = Column(DateTime(timezone=True))
    end_dtz = Column(DateTime(timezone=True))
