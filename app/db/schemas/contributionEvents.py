from datetime import datetime
from pydantic import BaseModel
import typing as t


class CheckBoxes(BaseModel):
    checkBoxes: t.List[str]


class CreateContributionEvent(BaseModel):
    projectName: str
    roundName: str
    title: str
    subtitle: str
    details: str
    checkBoxes: CheckBoxes
    # token details
    tokenId: str
    tokenName: str
    tokenDecimals: int
    tokenPrice: float
    proxyNFTId: str
    whitelistTokenId: str
    # others
    additionalDetails: dict
    # event table
    start_dtz: datetime
    end_dtz: datetime


class ContributionEvent(CreateContributionEvent):
    id: int
    eventId: int
    eventName: str

    class Config:
        orm_mode = True
