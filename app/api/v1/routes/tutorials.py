from fastapi import APIRouter, Depends, status
import typing as t
from starlette.responses import JSONResponse

from db.session import get_db
from db.crud.tutorials import (
    get_tutorials,
    get_unique_categories,
    create_tutorial,
    delete_tutorial,
    edit_tutorial,
)
from db.schemas.tutorials import CreateAndUpdateTutorial, Tutorial
from core.auth import get_current_active_user

tutorial_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Tutorial],
    response_model_exclude_none=True,
    name="tutorials:all-tutorials"
)
async def tutorials_list(
    category: str = 'all',
    db=Depends(get_db),
):
    """
    Get all Tutorials
    """
    try:
        return get_tutorials(db, category)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/categories",
    response_model=t.List[str],
    response_model_exclude_none=True,
    name="tutorials:all-categories"
)
async def tutorials_categories_list(
    db=Depends(get_db),
):
    """
    Get all Tutorials Categories
    """
    try:
        return get_unique_categories(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=Tutorial, response_model_exclude_none=True, name="tutorials:create")
async def tutorial_create(
    tutorial: CreateAndUpdateTutorial,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new tutorial
    """
    try:
        return create_tutorial(db, tutorial)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{tutorial_id}", response_model=Tutorial, response_model_exclude_none=True, name="tutorials:edit"
)
async def tutorial_edit(
    tutorial_id: int,
    tutorial: CreateAndUpdateTutorial,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing tutorial
    """
    try:
        return edit_tutorial(db, tutorial_id, tutorial)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{tutorial_id}", response_model=Tutorial, response_model_exclude_none=True, name="tutorial:delete"
)
async def tutorial_delete(
    tutorial_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete existing tutorial
    """
    try:
        return delete_tutorial(db, tutorial_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
