from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t

from db.models import jobs as models
from db.schemas import jobs as schemas


#################################
### CRUD OPERATIONS FOR JOBS ###
#################################


def get_job(db: Session, id: int):
    job = db.query(models.Jobs).filter(models.Jobs.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def get_jobs(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.Job]:
    return db.query(models.Jobs).offset(skip).limit(limit).all()


def create_job(db: Session, job: schemas.CreateAndUpdateJob):
    db_job = models.Jobs(
        title=job.title,
        shortDescription=job.shortDescription,
        description=job.description,
        category=job.category,
        archived=job.archived,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, id: int):
    job = get_job(db, id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.delete(job)
    db.commit()
    return job


def edit_job(
    db: Session, id: int, job: schemas.CreateAndUpdateJob
) -> schemas.Job:
    db_job = get_job(db, id)
    if not db_job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")
    update_data = job.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_job, key, value)

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job
