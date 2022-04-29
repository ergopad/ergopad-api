from pydantic import BaseModel
import datetime
import typing as t


class CreateAndUpdateNotification(BaseModel):
    transactionId: str
    transactionStatus: str
    context: str
    additionalText: str


class Notification(CreateAndUpdateNotification):
    id: int
    walletAddress: str
    createdTimestamp: datetime.datetime

    class Config:
        orm_mode = True