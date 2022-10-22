import typing as t
import datetime
import os

from fastapi import APIRouter, Depends, status
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.param_functions import File
from starlette.responses import JSONResponse
from core.auth import get_current_active_user
from db.session import get_db
from db.crud.projects import (
    get_projects,
    get_project,
    create_project,
    edit_project,
    delete_project
)
from db.schemas.projects import CreateAndUpdateProject, Project
from aws.s3 import AWS_REGION, S3, S3_BUCKET, S3_KEY

projects_router = r = APIRouter()

@r.get(
    "/",
    response_model=t.List[Project],
    response_model_exclude_none=True,
    name="projects:all-projects"
)
def projects_list(
    include_drafts: bool=False,
    db=Depends(get_db),
):
    """
    Get all projects
    """
    try:
        projects = get_projects(db, include_drafts)
        return projects
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/{id}",
    response_model=Project,
    response_model_exclude_none=True,
    name="projects:project-details"
)
def project_details(
    id: str,
    db=Depends(get_db),
):
    """
    Get any project details
    """
    try:
        return get_project(db, id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=Project, response_model_exclude_none=True, name="projects:create")
def project_create(
    project: CreateAndUpdateProject,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new project
    """
    try:
        return create_project(db, project)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{project_id}", response_model=Project, response_model_exclude_none=True, name="projects:edit"
)
def project_edit(
    project_id: int,
    project: CreateAndUpdateProject,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Update existing project
    """
    try:
        return edit_project(db, project_id, project)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{project_id}", response_model=Project, response_model_exclude_none=True, name="projects:delete"
)
def project_delete(
    project_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete existing project
    """
    try:
        return delete_project(db, project_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/upload_image", name="projects:upload-image-to-S3")
def upload(fileobject: UploadFile = File(...), current_user=Depends(get_current_active_user)):
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
