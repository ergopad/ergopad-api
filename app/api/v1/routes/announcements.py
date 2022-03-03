from fastapi import APIRouter, Depends
import typing as t

from core.auth import get_current_active_superuser

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
    announcements = get_announcements(db)
    return announcements


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
    return get_announcement(db, id)


@r.post("/", response_model=Announcement, response_model_exclude_none=True, name="announcements:create")
async def announcement_create(
    announcement: CreateAndUpdateAnnouncement,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new announcement
    """
    return create_announcement(db, announcement)


@r.put(
    "/{announcement_id}", response_model=Announcement, response_model_exclude_none=True, name="announcements:edit"
)
async def announcement_edit(
    announcement_id: int,
    announcement: CreateAndUpdateAnnouncement,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    """
    Update existing announcement
    """
    return edit_announcement(db, announcement_id, announcement)


@r.delete(
    "/{announcement_id}", response_model=Announcement, response_model_exclude_none=True, name="announcements:delete"
)
async def announcement_delete(
    announcement_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing announcement
    """
    return delete_announcement(db, announcement_id)
