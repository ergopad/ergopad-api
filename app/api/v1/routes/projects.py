from fastapi import APIRouter, Request, Depends, Response, encoders
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.param_functions import File

import typing as t
import datetime
import os

from core.auth import get_current_active_superuser

from db.session import get_db
from db.crud.projects import (
    get_project_team,
    get_projects,
    get_project,
    create_project,
    edit_project,
    delete_project
)
from db.schemas.projects import CreateAndUpdateProjectWithTeam, Project, ProjectWithTeam

from aws.s3 import AWS_REGION, S3, S3_BUCKET, S3_KEY

projects_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Project],
    response_model_exclude_none=True,
    name="projects:all-projects"
)
async def projects_list(
    response: Response,
    db=Depends(get_db),
):
    """
    Get all projects
    """
    projects = get_projects(db)
    return projects


@r.get(
    "/{project_id}",
    response_model=ProjectWithTeam,
    response_model_exclude_none=True,
    name="projects:project-details"
)
async def project_details(
    request: Request,
    project_id: int,
    db=Depends(get_db),
):
    """
    Get any project details
    """
    project = get_project(db, project_id)
    project_team = get_project_team(db, project_id)
    return ProjectWithTeam(
        id=project.id,
        name=project.name,
        fundsRaised=project.fundsRaised,
        shortDescription=project.shortDescription,
        description=project.description,
        socials=project.socials,
        bannerImgUrl=project.bannerImgUrl,
        isLaunched=project.isLaunched,
        team=project_team
    )


@r.post("/", response_model=ProjectWithTeam, response_model_exclude_none=True, name="projects:create")
async def project_create(
    request: Request,
    project: CreateAndUpdateProjectWithTeam,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new project
    """
    return create_project(db, project)


@r.put(
    "/{project_id}", response_model=ProjectWithTeam, response_model_exclude_none=True, name="projects:edit"
)
async def project_edit(
    request: Request,
    project_id: int,
    project: CreateAndUpdateProjectWithTeam,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    """
    Update existing project
    """
    return edit_project(db, project_id, project)


@r.delete(
    "/{project_id}", response_model=Project, response_model_exclude_none=True, name="projects:delete"
)
async def project_delete(
    request: Request,
    project_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing project
    """
    return delete_project(db, project_id)


@r.post("/upload_image", name="projects:upload-image-to-S3")
async def upload(fileobject: UploadFile = File(...), current_user=Depends(get_current_active_superuser)):
    """
    Upload files to s3 bucket
    """
    filename = fileobject.filename
    current_time = datetime.datetime.now()
    # split the file name into two different path (string + extention)
    split_file_name = os.path.splitext(filename)
    # for realtime application you must have genertae unique name for the file
    file_name_unique = split_file_name[0] + "." + \
        str(current_time.timestamp()).replace('.', '')
    file_extension = split_file_name[1]  # file extention
    data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
    filename_mod = S3_KEY + "." + file_name_unique + file_extension
    uploads3 = S3.Bucket(S3_BUCKET).put_object(
        Key=filename_mod, Body=data, ACL='public-read')
    if uploads3:
        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename_mod}"
        return {"status": "success", "image_url": s3_url}  # response added
    else:
        raise HTTPException(status_code=400, detail="Failed to upload in S3")
