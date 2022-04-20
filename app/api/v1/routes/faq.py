from fastapi import APIRouter, Depends, status
import typing as t
from starlette.responses import JSONResponse

from db.session import get_db
from db.crud.faq import (
    get_faqs,
    create_faq,
    delete_faq,
    edit_faq,
)
from db.schemas.faq import CreateAndUpdateFaq, Faq
from core.auth import get_current_active_user

faq_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Faq],
    response_model_exclude_none=True,
    name="faq:all-faqs"
)
async def faqs_list(
    tag: str = 'all',
    db=Depends(get_db),
):
    """
    Get all Faqs
    """
    try:
        return get_faqs(db, tag)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/", response_model=Faq, response_model_exclude_none=True, name="faq:create")
async def faq_create(
    faq: CreateAndUpdateFaq,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new faq
    """
    try:
        return create_faq(db, faq)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{faq_id}", response_model=Faq, response_model_exclude_none=True, name="faq:edit"
)
async def faq_edit(
    faq_id: int,
    faq: CreateAndUpdateFaq,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing faq
    """
    try:
        return edit_faq(db, faq_id, faq)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{faq_id}", response_model=Faq, response_model_exclude_none=True, name="faq:delete"
)
async def faq_delete(
    faq_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete existing faq
    """
    try:
        return delete_faq(db, faq_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
