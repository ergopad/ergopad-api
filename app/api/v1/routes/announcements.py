from fastapi import APIRouter, Depends, status
import typing as t
from starlette.responses import JSONResponse

from core.auth import get_current_active_user

from db.session import get_db
from db.crud.announcements import (
    get_announcements,
    get_announcement,
    create_announcement,
    edit_announcement,
    delete_announcement
)
from db.schemas.announcements import CreateAndUpdateAnnouncement, Announcement

announcement_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Announcement],
    response_model_exclude_none=True,
    name="announcements:all-announcements"
)
async def announcements_list(
    db=Depends(get_db),
):
    """
    Get all announcements
    """
    try:
        return get_announcements(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/{id}",
    response_model=Announcement,
    response_model_exclude_none=True,
    name="announcements:announcement-details"
)
async def announcement_details(
    id: str,
    db=Depends(get_db),
):
    """
    Get any announcement details
    """
    try:
        return get_announcement(db, id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=Announcement, response_model_exclude_none=True, name="announcements:create")
async def announcement_create(
    announcement: CreateAndUpdateAnnouncement,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new announcement
    """
    try:
        return create_announcement(db, announcement)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{announcement_id}", response_model=Announcement, response_model_exclude_none=True, name="announcements:edit"
)
async def announcement_edit(
    announcement_id: int,
    announcement: CreateAndUpdateAnnouncement,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Update existing announcement
    """
    try:
        return edit_announcement(db, announcement_id, announcement)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{announcement_id}", response_model=Announcement, response_model_exclude_none=True, name="announcements:delete"
)
async def announcement_delete(
    announcement_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete existing announcement
    """
    try:
        return delete_announcement(db, announcement_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
