from pydantic import BaseModel
import datetime
import typing as t


class CreateAndUpdateNotification(BaseModel):
    transactionId: t.Optional[str]
    transactionStatus: t.Optional[str]
    context: t.Optional[str]
    additionalText: t.Optional[str]


class Notification(CreateAndUpdateNotification):
    id: int
    walletAddress: str
    createdTimestamp: datetime.datetime

    class Config:
        orm_mode = True
