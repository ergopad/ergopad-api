from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from db.session import Base

# NOTIFICATION MODEL


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    walletAddress = Column(String, index=True)
    createdTimestamp = Column(DateTime(timezone=True),
                              server_default=func.now())
    transactionId = Column(String)
    transactionStatus = Column(String)
    context = Column(String)
    additionalText = Column(String)
