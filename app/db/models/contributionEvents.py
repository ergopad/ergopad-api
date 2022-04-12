from sqlalchemy import Column, Float, Integer, String, JSON

from db.session import Base

# contributionEvent MODEL


class ContributionEvent(Base):
    __tablename__ = "contributionEvents"

    id = Column(Integer, primary_key=True, index=True)
    projectName = Column(String)
    roundName = Column(String)
    eventId = Column(Integer)
    title = Column(String)
    subtitle = Column(String)
    details = Column(String)
    checkBoxes = Column(JSON)
    tokenId = Column(String)
    tokenName = Column(String)
    tokenDecimals = Column(Integer)
    tokenPrice = Column(Float)
    proxyNFTId = Column(String)
    whitelistTokenId = Column(String)
    additionalDetails = Column(JSON)
