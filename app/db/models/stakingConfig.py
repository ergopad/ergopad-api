from sqlalchemy import Column, Float, Integer, String, JSON

from db.session import Base

# staking MODEL


class StakingConfig(Base):
    __tablename__ = "stakingConfig"

    id = Column(Integer, primary_key=True, index=True)
    project = Column(String)
    title = Column(String)
    tokenId = Column(String)
    stakingInfo = Column(String)
    terms = Column(String)
    additionalDetails = Column(JSON)
