import typing as t
from fastapi import APIRouter, Request, Depends, Response, status
from starlette.responses import JSONResponse
from db.session import get_db
from db.crud.users import (
    get_users,
    get_user,
    create_user,
    delete_user,
    edit_user,
)
from db.schemas.users import UserCreate, UserEdit, User
from core.auth import get_current_active_user, get_current_active_superuser

users_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[User],
    response_model_exclude_none=True,
    name="users:all-users"
)
async def users_list(
    response: Response,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get all users
    """
    try:
        users = get_users(db)
        # This is necessary for react-admin to work
        response.headers["Content-Range"] = f"0-9/{len(users)}"
        return users
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get("/me", response_model=User, response_model_exclude_none=True, name="users:me")
async def user_me(current_user=Depends(get_current_active_user)):
    """
    Get own user
    """
    return current_user


@r.get(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
    name="users:user-details"
)
async def user_details(
    request: Request,
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get any user details
    """
    try:
        return get_user(db, user_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=User, response_model_exclude_none=True, name="users:create")
async def user_create(
    request: Request,
    user: UserCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new user
    """
    try:
        return create_user(db, user)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{user_id}", response_model=User, response_model_exclude_none=True, name="users:edit"
)
async def user_edit(
    request: Request,
    user_id: int,
    user: UserEdit,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Update existing user
    """
    try:
        return edit_user(db, user_id, user)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{user_id}/password", response_model=User, response_model_exclude_none=True, name="users:change-password"
)
async def user_edit(
    request: Request,
    user_id: int,
    user: UserEdit,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update user password
    """
    try:
        if (user_id == current_user.id and user.is_active == current_user.is_active and user.is_superuser == current_user.is_superuser):
            return edit_user(db, user_id, user)
        else:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=f'Not authorized to change other user data fields')
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{user_id}", response_model=User, response_model_exclude_none=True, name="users:delete"
)
async def user_delete(
    request: Request,
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing user
    """
    try:
        return delete_user(db, user_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
