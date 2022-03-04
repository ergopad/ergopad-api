from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t

from db.models import announcements as models
from db.schemas import announcements as schemas


#########################################
### CRUD OPERATIONS FOR ANNOUNCEMENTS ###
#########################################


def generate_announcement_slug(title: str) -> str:
    title = ''.join(
        list(filter(lambda c: c.isalnum() or c == ' ', list(title.lower()))))
    return (''.join(title.split()), '_'.join(title.split()))


def get_announcement(db: Session, id: str):
    announcement = None
    id = str(id)
    if (id.isdecimal()):
        # get by id
        announcement = db.query(models.Announcement).filter(
            models.Announcement.id == int(id)).first()
    else:
        # get by slug
        announcements = list(filter(lambda ann: id in generate_announcement_slug(ann.title),
                                    db.query(models.Announcement).all()))
        if len(announcements):
            announcement = announcements[0]
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


def get_announcements(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.Announcement]:
    return db.query(models.Announcement).order_by(models.Announcement.createdTimestamp).offset(skip).limit(limit).all()


def create_announcement(db: Session, announcement: schemas.CreateAndUpdateAnnouncement):
    db_announcement = models.Announcement(
        title=announcement.title,
        shortDescription=announcement.shortDescription,
        description=announcement.description,
        bannerImgUrl=announcement.bannerImgUrl,
        tag=announcement.tag,
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement


def delete_announcement(db: Session, id: int):
    announcement = get_announcement(db, id)
    if not announcement:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="Announcement not found")
    db.delete(announcement)
    db.commit()
    return announcement


def edit_announcement(
    db: Session, id: int, announcement: schemas.CreateAndUpdateAnnouncement
) -> schemas.Announcement:
    db_announcement = get_announcement(db, id)
    if not db_announcement:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="Announcement not found")

    update_data = announcement.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_announcement, key, value)

    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement
