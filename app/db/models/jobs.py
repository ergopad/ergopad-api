from sqlalchemy import Boolean, Column, Integer, String

from db.session import Base

# JOBS MODEL


class Jobs(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    shortDescription = Column(String)
    description = Column(String)
    category = Column(String)
    archived = Column(Boolean)
