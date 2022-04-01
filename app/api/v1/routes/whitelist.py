import inspect
import logging
import pandas as pd
import typing as t
from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from fastapi import APIRouter, Depends, status, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from time import time
from datetime import datetime as dt
from api.v1.routes.staking import staked, AddressList
from db.crud.whitelist_events import create_whitelist_event, delete_whitelist_event, edit_whitelist_event, get_whitelist_event_by_name, get_whitelist_events
from db.session import get_db
from db.schemas.whitelistEvents import CreateWhitelistEvent, WhitelistEvent
from core.security import get_md5_hash
from core.auth import get_current_active_superuser
from config import Config, Network  # api specific config

CFG = Config[Network]

whitelist_router = r = APIRouter()

# region BLOCKHEADER
"""
Whitelist API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20220111
Purpose: allow wallets to be whitelisted
Contributor(s): https://github.com/Luivatra

Notes: 
"""
# endregion BLOCKHEADER

# region INIT
DEBUG = CFG.debug
DATABASE = CFG.connectionString
DATEFORMAT = '%m/%d/%Y %H:%M'
headers = {'Content-Type': 'application/json'}
# NOW = int(time()) # !! NOTE: can't use here; will only update once if being imported
MIN_ERGOPAD_VALUE_FOR_STAKER = 1000
# endregion INIT

# region LOGGING
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)


def myself(): return inspect.stack()[1][3]
# endregion LOGGING


# region CLASSES

# Whitelist Request Model
class Whitelist(BaseModel):
    ergoAddress: str  # wallet
    email: str
    event: str
    name: str
    sigValue: float
    socialHandle: str
    socialPlatform: str
    chatHandle: str
    chatPlatform: str

    class Config:
        schema_extra = {
            "example": {
                'ergoAddress': '3WzKuUxmG7HtfmZNxxHw3ArPzsZZR96yrNkTLq4i1qFwVqBXAU8X',
                'email': 'hello@world.com',
                'event': 'IDO',
                'name': 'Jo Smith',
                'sigValue': 2000.5,
                'socialHandle': '@tweetyBird',
                'socialPlatform': 'twitter',
                'chatHandle': '@puddyTat',
                'chatPlatform': 'discord',
            }
        }
# endregion CLASSES


# region ROUTES

# TODO: update /signup route
# 1. Switch from pd.Dataframe().to_sql
# 2. rewrite logic for max sigusd allowance
@r.post("/signup", name="whitelist:signup")
async def whitelistSignUp(whitelist: Whitelist, request: Request):
    NOW = int(time())
    try:
        eventName = whitelist.event
        logging.debug(DATABASE)
        con = create_engine(DATABASE)
        logging.debug('sql')
        sql = f"""
            with wht as (
                select "eventId"
                    , coalesce(sum("allowance_sigusd"), 0.0) as allowance_sigusd
                    , coalesce(sum("spent_sigusd"), 0.0) as spent_sigusd
                from whitelist
                group by "eventId"
            )
            select 
                name
                , evt.id
                , description
                , total_sigusd
                , buffer_sigusd
                , start_dtz
                , end_dtz
                , "individualCap"
                , coalesce(allowance_sigusd, 0.0) as allowance_sigusd
                , coalesce(spent_sigusd, 0.0) as spent_sigusd
            from "events" evt
                left join wht on wht."eventId" = evt.id
            where evt.name = {eventName!r}
                and evt."isWhitelist" = 1
        """
        # logging.debug(sql)
        res = con.execute(sql).fetchone()
        # logging.debug(f'res: {res}')

        # event not found
        if res == None or len(res) == 0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'whitelist event, {eventName} not found.')

        # is valid signup window?
        if (NOW < int(res['start_dtz'].timestamp())) or (NOW > int(res['end_dtz'].timestamp())):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist signup between {res['start_dtz']} and {res['end_dtz']}.")

        # is funding complete?
        if res['allowance_sigusd'] >= (res['total_sigusd'] + res['buffer_sigusd']):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist funds complete.")

        # special checks
        validation = await checkEventConstraints(whitelist)
        if not validation[0]:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist signup failed. {validation[1]}")

        logging.debug(
            f"Current funding: {100*res['allowance_sigusd']/(res['total_sigusd']+res['buffer_sigusd']):.2f}% ({res['allowance_sigusd']} of {res['total_sigusd']+res['buffer_sigusd']})")
        eventId = res['id']
        whitelist.sigValue = int(whitelist.sigValue)

        # does individual cap exceed?
        if whitelist.sigValue > res['individualCap']:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist signup individual cap is {res['individualCap']} sigUSD")

        # sigValue 0 check
        if whitelist.sigValue <= 0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"Invalid SigUSD value.")

        # find wallet
        logging.debug(f'connecting to: {CFG.connectionString}')
        con = create_engine(DATABASE)
        logging.debug('connected to database...')
        pd.options.mode.chained_assignment = None  # default='warn'
        df = pd.DataFrame(jsonable_encoder(whitelist), index=[0])
        logging.debug(f'dataframe: {df}')
        sqlFindWallet = f"select id from wallets where address = '{whitelist.ergoAddress}'"
        logging.debug(sqlFindWallet)
        res = con.execute(sqlFindWallet)

        # create wallet if it doesn't exist
        if res.rowcount == 0:
            dfWallet = df[['ergoAddress', 'email', 'socialHandle',
                           'socialPlatform', 'chatHandle', 'chatPlatform']]
            dfWallet['network'] = Network
            dfWallet['lastSeen_dtz'] = dt.fromtimestamp(
                NOW).strftime(DATEFORMAT)
            dfWallet['created_dtz'] = dt.fromtimestamp(
                NOW).strftime(DATEFORMAT)
            dfWallet = dfWallet.rename(columns={'ergoAddress': 'address'})
            logging.debug(f'save wallet: {dfWallet}')
            dfWallet.to_sql('wallets', con=con,
                            if_exists='append', index=False)

        # check this wallet has not already registered for this event
        res = con.execute(sqlFindWallet).fetchone()
        walletId = res['id']
        sqlAlreadyWhitelisted = f'select id from "whitelist" where "walletId" = {walletId} and "eventId" = {eventId}'
        res = con.execute(sqlAlreadyWhitelisted)
        if res.rowcount == 0:
            # add whitelist entry
            # TODO: clean up logic
            logging.debug(f'found id: {walletId}')
            dfWhitelist = df[['sigValue']]
            dfWhitelist['walletId'] = walletId
            dfWhitelist['eventId'] = eventId
            dfWhitelist['isWhitelist'] = 1
            dfWhitelist['created_dtz'] = dt.fromtimestamp(
                NOW).strftime(DATEFORMAT)
            dfWhitelist = dfWhitelist.rename(
                columns={'sigValue': 'allowance_sigusd'})
            # ? why
            dfWhitelist['lastAssemblerStatus'] = dfWhitelist['allowance_sigusd']
            # dfWhitelist['allowance_sigusd'] = 20000
            dfWhitelist.to_sql('whitelist', con=con,
                               if_exists='append', index=False)

            # log ip hash for analytics and backend filtering
            # secure bcrypt one way hash
            ipHash = get_md5_hash(request.client.host)
            dfEventsIp = pd.DataFrame({
                "walletId": [walletId],
                "eventId": [eventId],
                "ipHash": [ipHash]
            })
            logging.debug(f'save ipHash: {dfEventsIp}')
            dfEventsIp.to_sql('eventsIp', con=con,
                              if_exists='append', index=False)

            # whitelist success
            return {'status': 'success', 'detail': f'added to whitelist: SigUSD value: {whitelist.sigValue}'}

        # already whitelisted
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'wallet already signed up for this event')

    except Exception as e:
        logging.error(f'ERR:{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to save whitelist request ({e})')


async def checkEventConstraints(whitelist: Whitelist):
    # Check special contraints for events
    # return True if valid else return (False, reason)
    if whitelist.event == 'staker-seed-paideia-202203wl':
        # make sure address has ergopad staked
        address = whitelist.ergoAddress
        try:
            stakedRes = await staked(AddressList(addresses=[address]))
            if stakedRes["totalStaked"] >= MIN_ERGOPAD_VALUE_FOR_STAKER:
                return (True, "ok")
            else:
                return (False, f"Not enough ergopad staked for this address. Min stake required is {MIN_ERGOPAD_VALUE_FOR_STAKER}.")
        except:
            return (False, "Explorer API failed. Could not validate if enough ergopad is staked.")
    else:
        return (True, "ok")


@r.get("/info/{eventName}", name="whitelist:info")
async def whitelistInfo(eventName):
    NOW = int(time())
    try:
        logging.debug(DATABASE)
        con = create_engine(DATABASE)
        sql = f"""
            with wht as (
                select "eventId"
                    , coalesce(sum("allowance_sigusd"), 0.0) as allowance_sigusd
                    , coalesce(sum("spent_sigusd"), 0.0) as spent_sigusd
                from whitelist
                group by "eventId"
            )
            select 
                name
                , description
                , total_sigusd
                , buffer_sigusd
                , start_dtz
                , end_dtz
                , coalesce(allowance_sigusd, 0.0) as allowance_sigusd
                , coalesce(spent_sigusd, 0.0) as spent_sigusd
            from "events" evt
                left join wht on wht."eventId" = evt.id
            where evt.name = {eventName!r}
        """
        # logging.debug(sql)
        res = con.execute(sql).fetchone()
        logging.debug(res)
        return {
            'status': 'success',
            'now': NOW,
            'isBeforeSignup': NOW < int(res['start_dtz'].timestamp()),
            'isAfterSignup': NOW > int(res['end_dtz'].timestamp()),
            'isFundingComplete': res['allowance_sigusd'] >= (res['total_sigusd'] + res['buffer_sigusd']),
            'name': res['name'],
            'description': res['description'],
            'total_sigusd': res['total_sigusd'],
            'buffer_sigusd': res['buffer_sigusd'],
            'start_dtz': int(res['start_dtz'].timestamp()),
            'end_dtz': int(res['end_dtz'].timestamp()),
            'allowance_sigusd': int(res['allowance_sigusd']),
            'spent_sigusd': int(res['spent_sigusd']),
            'gmt': NOW
        }

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid whitelist request ({e})')


@r.get(
    "/events",
    response_model_exclude_none=True,
    name="whitelist:all-events"
)
async def whitelist_event_list(
    db=Depends(get_db),
):
    """
    Get all events
    """
    try:
        return get_whitelist_events(db)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/events/{projectName}/{roundName}",
    response_model_exclude_none=True,
    name="whitelist:event"
)
async def whitelist_event(projectName: str, roundName: str,
                          db=Depends(get_db),
                          ):
    """
    Get event
    """
    try:
        return get_whitelist_event_by_name(db, projectName, roundName)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/events", response_model_exclude_none=True, name="whitelist:create-event")
async def whitelist_event_create(
    whitelist_event: CreateWhitelistEvent,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new event
    """
    try:
        return create_whitelist_event(db, whitelist_event)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/events/{id}", response_model_exclude_none=True, name="whitelist:edit-event"
)
async def whitelist_event_edit(
    id: int,
    whitelist_event: CreateWhitelistEvent,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    """
    Update existing event
    """
    return edit_whitelist_event(db, id, whitelist_event)


@r.delete(
    "/{id}", response_model_exclude_none=True, name="whitelist:delete-event"
)
async def whitelist_event_delete(
    id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete event
    """
    try:
        return delete_whitelist_event(db, id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')

# endregion ROUTES

# MAIN
if __name__ == '__main__':
    print('API routes: ...')
