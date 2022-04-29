from fastapi import APIRouter, Depends, status
import typing as t
from starlette.responses import JSONResponse

from core.auth import get_current_active_user

from db.session import get_db
from db.crud.notifications import (
    cleanup_notifications,
    create_notification,
    delete_notification,
    get_notifications
)
from db.schemas.notifications import CreateAndUpdateNotification, Notification

notification_router = r = APIRouter()


@r.get(
    "/{walletAddress}",
    response_model=t.List[Notification],
    response_model_exclude_none=True,
    name="notifications:all-notifications"
)
async def notifications_list(
    walletAddress: str,
    db=Depends(get_db),
):
    """
    Get all notifications for a single address
    """
    try:
        return get_notifications(db, [walletAddress])
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post(
    "/getNotifications",
    response_model=t.List[Notification],
    response_model_exclude_none=True,
    name="notifications:all-notifications"
)
async def notifications_list(
    walletAddresses: t.List[str],
    db=Depends(get_db),
):
    """
    Get all notifications
    """
    try:
        return get_notifications(db, walletAddresses)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/{walletAddress}", response_model=Notification, response_model_exclude_none=True, name="notifications:create")
async def notification_create(
    walletAddress: str,
    notification: CreateAndUpdateNotification,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new notification
    """
    try:
        return create_notification(db, walletAddress, notification)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/cleanup", name="notifications:clean-up"
)
async def notification_cleanup(
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete old notifcations for all users
    """
    try:
        return cleanup_notifications(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{notification_id}", response_model=Notification, response_model_exclude_none=True, name="notifications:delete"
)
async def notification_delete(
    notification_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete existing notification
    """
    try:
        return delete_notification(db, notification_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
