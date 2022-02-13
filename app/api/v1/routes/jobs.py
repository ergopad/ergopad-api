from fastapi import APIRouter, Request, Depends
import typing as t

from db.session import get_db
from db.crud.jobs import (
    get_jobs,
    get_job,
    create_job,
    delete_job,
    edit_job,
)
from db.schemas.jobs import CreateAndUpdateJob, Job
from core.auth import get_current_active_superuser

jobs_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Job],
    response_model_exclude_none=True,
    name="jobs:all-jobs"
)
async def jobs_list(
    db=Depends(get_db),
):
    """
    Get all jobs
    """
    return get_jobs(db)


@r.get(
    "/{job_id}",
    response_model=Job,
    response_model_exclude_none=True,
    name="jobs:job-details"
)
async def job_details(
    job_id: int,
    db=Depends(get_db),
):
    """
    Get any job details
    """
    return get_job(db, job_id)


@r.post("/", response_model=Job, response_model_exclude_none=True, name="jobs:create")
async def job_create(
    job: CreateAndUpdateJob,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new job
    """
    return create_job(db, job)


@r.put(
    "/{job_id}", response_model=Job, response_model_exclude_none=True, name="jobs:edit"
)
async def job_edit(
    job_id: int,
    job: CreateAndUpdateJob,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Update existing job
    """
    return edit_job(db, job_id, job)


@r.delete(
    "/{job_id}", response_model=Job, response_model_exclude_none=True, name="jobs:delete"
)
async def job_delete(
    job_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing job
    """
    return delete_job(db, job_id)
