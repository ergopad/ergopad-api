from fastapi import APIRouter, Depends
import typing as t

from db.session import get_db
from db.crud.faq import (
    get_faqs,
    create_faq,
    delete_faq,
    edit_faq,
)
from db.schemas.faq import CreateAndUpdateFaq, Faq
from core.auth import get_current_active_superuser

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
    return get_faqs(db, tag)


@r.post("/", response_model=Faq, response_model_exclude_none=True, name="faq:create")
async def faq_create(
    faq: CreateAndUpdateFaq,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new faq
    """
    return create_faq(db, faq)


@r.put(
    "/{faq_id}", response_model=Faq, response_model_exclude_none=True, name="faq:edit"
)
async def faq_edit(
    faq_id: int,
    faq: CreateAndUpdateFaq,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Update existing faq
    """
    return edit_faq(db, faq_id, faq)


@r.delete(
    "/{faq_id}", response_model=Faq, response_model_exclude_none=True, name="faq:delete"
)
async def faq_delete(
    faq_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing faq
    """
    return delete_faq(db, faq_id)
