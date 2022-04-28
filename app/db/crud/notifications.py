import datetime
from operator import mod
from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy import delete
from sqlalchemy.orm import Session
import typing as t

from db.models import notifications as models
from db.schemas import notifications as schemas

#########################################
### CRUD OPERATIONS FOR NOTIFICATIONS ###
#########################################


def get_notifications(
    db: Session, walletAddresses: t.List[str], skip: int = 0, limit: int = 10
) -> t.List[schemas.Notification]:
    return db.query(models.Notification).filter(
        models.Notification.walletAddress.in_(walletAddresses)).order_by(
            models.Notification.createdTimestamp).offset(skip).limit(limit).all()


def create_notification(db: Session, walletAddress: str, notification: schemas.CreateAndUpdateNotification):
    db_notification = models.Notification(
        walletAddress=walletAddress,
        transactionId=notification.transactionId,
        transactionStatus=notification.transactionStatus,
        context=notification.context,
        additionalText=notification.additionalText
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def delete_notification(db: Session, id: int):
    notification = db.query(models.Notification).filter(
        models.Notification.id == id).first()
    if not notification:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content="Notification not found")
    db.delete(notification)
    db.commit()
    return notification


def cleanup_notifications(db: Session):
    date = datetime.datetime.utcnow() - datetime.timedelta(30)
    ret = {
        "deleted_rows": db.query(models.Notification).filter(models.Notification.createdTimestamp > date).delete()
    }
    db.commit()
    return ret
