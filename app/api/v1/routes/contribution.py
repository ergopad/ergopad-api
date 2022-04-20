import inspect
import logging
from starlette.responses import JSONResponse
from fastapi import APIRouter, Depends, status
from db.schemas.contributionEvents import CreateContributionEvent
from db.crud.contribution_events import create_contribution_event, delete_contribution_event, edit_contribution_event, get_contribution_event_by_name, get_contribution_events
from db.session import get_db
from core.auth import get_current_active_user
from config import Config, Network  # api specific config

CFG = Config[Network]
DEBUG = CFG.debug

contribution_router = r = APIRouter()


levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)


def myself(): return inspect.stack()[1][3]


@r.get(
    "/events",
    response_model_exclude_none=True,
    name="contribution:all-events"
)
async def contribution_event_list(
    db=Depends(get_db),
):
    """
    Get all events
    """
    try:
        return get_contribution_events(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/events/{projectName}/{roundName}",
    response_model_exclude_none=True,
    name="contribution:event"
)
async def contribution_event(projectName: str, roundName: str,
                             db=Depends(get_db),
                             ):
    """
    Get event
    """
    try:
        return get_contribution_event_by_name(db, projectName, roundName)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/events", response_model_exclude_none=True, name="contribution:create-event")
async def contribution_event_create(
    contribution_event: CreateContributionEvent,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new event
    """
    try:
        return create_contribution_event(db, contribution_event)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/events/{id}", response_model_exclude_none=True, name="contribution:edit-event"
)
async def contribution_event_edit(
    id: int,
    contribution_event: CreateContributionEvent,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Update existing event
    """
    try:
        return edit_contribution_event(db, id, contribution_event)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/events/{id}", response_model_exclude_none=True, name="contribution:delete-event"
)
async def contribution_event_delete(
    id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete event
    """
    try:
        return delete_contribution_event(db, id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
