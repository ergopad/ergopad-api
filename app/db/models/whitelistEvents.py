from sqlalchemy import Column, Integer, String, JSON

from db.session import Base

# whitelistEvent MODEL


class WhitelistEvent(Base):
    __tablename__ = "whitelistEvents"

    id = Column(Integer, primary_key=True, index=True)
    projectName = Column(String)
    roundName = Column(String)
    eventId = Column(Integer)
    title = Column(String)
    subtitle = Column(String)
    details = Column(String)
    checkBoxes = Column(JSON)
    additionalDetails = Column(JSON)
