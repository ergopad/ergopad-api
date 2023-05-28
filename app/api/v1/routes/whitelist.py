import inspect
import logging
import time
import typing as t

from datetime import datetime as dt

from starlette.responses import JSONResponse
from sqlalchemy import create_engine, text
from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel

from api.v1.routes.staking import staked, AddressList
from db.crud.whitelist_events import create_whitelist_event, delete_whitelist_event, edit_whitelist_event, get_whitelist_event_by_event_id, get_whitelist_event_by_name, get_whitelist_events
from db.crud.cardano_metadata_whitelist_ext import create_metadata, get_metadata
from db.session import get_db
from db.schemas.whitelistEvents import CreateWhitelistEvent, WhitelistEvent
from db.schemas.cardano_metadata_whitelist_ext import CreateOrUpdateCardanoMetadataWhitelistExt
from core.security import get_md5_hash
from core.auth import get_current_active_user
from config import Config, Network  # api specific config
from db.session import engine

CFG = Config[Network]

whitelist_router = r = APIRouter()

# region INIT
DEBUG = CFG.debug
DATABASE = CFG.connectionString
DATEFORMAT = '%m/%d/%Y %H:%M:%S.%f'
headers = {'Content-Type': 'application/json'}
# NOW = int(time.time()) # !! NOTE: can't use here; will only update once if being imported
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
    ergoAddress: t.Optional[str]
    adaAddresses: t.List[str] = []
    kycApproval: bool = False
    email: str = "__unknown"
    event: str
    name: str = "__anon_ergonaut"
    sigValue: t.Optional[float] # @Deprecated
    usdValue: t.Optional[float]
    tpe: str = "ergo"   # ergo or cardano

# endregion CLASSES


# region ROUTES
@r.get("/checkIp")
def go(request: Request):
    # return {}
    logging.debug(request.client.host)
    return {
        'ip': request.client.host,
        'hash': get_md5_hash(request.client.host)
    }

# TODO: update /signup route
# 1. Switch from pd.Dataframe().to_sql
# 2. rewrite logic for max sigusd allowance
@r.post("/signup", name="whitelist:signup")
def whitelistSignUp(whitelist: Whitelist, request: Request):
    print(whitelist)
    NOW = time.time()
    try:
        # validate stuff
        whitelist = backfill_usd_value(whitelist)
        if whitelist.tpe == "ergo" and whitelist.ergoAddress == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="ergoAddress is null")
        if whitelist.tpe == "cardano" and len(whitelist.adaAddresses) == 0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="adaAddresses is empty")
        # replacing ergo address field with hash of ada addresses
        # this is to make existing checks work with cardano
        if whitelist.tpe == "cardano":
            address_hash = get_ada_address_hash(whitelist.adaAddresses)
            whitelist.ergoAddress = address_hash

        # get eventId
        eventName = whitelist.event
        logging.debug('sql')
        sql = text(f"""
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
            where evt.name = :eventName
                and evt."isWhitelist" = 1
        """)
        with engine.begin() as con:
            res = con.execute(sql, {'eventName': eventName}).fetchone()

        # event not found
        if res == None or len(res) == 0:
            logging.warning(f'whitelist event, {eventName} not found.')
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'whitelist event, {eventName} not found.')
        eventId = res['id']

        # is valid signup window?
        if (int(NOW) < int(res['start_dtz'].timestamp())) or (int(NOW) > int(res['end_dtz'].timestamp())):
            logging.warning(f"whitelist signup between {res['start_dtz']} and {res['end_dtz']}.")
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist signup between {res['start_dtz']} and {res['end_dtz']}.")

        # is funding complete?
        # do not check for funding complete for staker snapshots
        if (res['allowance_sigusd'] >= (res['total_sigusd'] + res['buffer_sigusd'])) and not isStakerSnapshotWhitelist(eventId):
            logging.warning(f"whitelist funds complete.")
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist funds complete.")

        # special checks
        validation = checkEventConstraints(eventId, whitelist)
        if not validation[0]:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist signup failed. {validation[1]}")

        # calculate funding
        logging.debug(f"Current funding: {100*res['allowance_sigusd']/(res['total_sigusd']+res['buffer_sigusd']):.2f}% ({res['allowance_sigusd']} of {res['total_sigusd']+res['buffer_sigusd']})")

        whitelist.sigValue = int(whitelist.sigValue)
        # does individual cap exceed?
        if whitelist.sigValue > res['individualCap']:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"whitelist signup individual cap is {res['individualCap']} sigUSD")

        # sigValue 0 check
        if whitelist.sigValue <= 0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f"Invalid SigUSD value.")

        # continue with signup
        sqlFindWallet = text(f"select id from wallets where address = :address")
        resFindWallet = None
        with engine.begin() as con:
            resFindWallet = con.execute(sqlFindWallet, {'address': whitelist.ergoAddress}).fetchone()
        # logging.debug(f'find wallet: {resFindWallet["id"]}')

        # does wallet exist, or do we need to create it?
        if resFindWallet is None:
            sql = text(f'''
                insert into wallets(address, email, "blockChainId", network, "walletPass", mneumonic, "socialHandle", "socialPlatform", "chatHandle", "chatPlatform", created_dtz, "lastSeen_dtz", "twitterHandle", "discordHandle", "telegramHandle")
	            values (
                    :address -- address
                    , null -- email
                    , null -- blockChainId
                    , :network -- network
                    , null, null -- walletPass, mneumonic
                    , null, null -- socials                    
                    , null, null -- chat                    
                    , {dt.fromtimestamp(NOW).strftime(DATEFORMAT)!r} -- created_dtz
                    , {dt.fromtimestamp(NOW).strftime(DATEFORMAT)!r} -- lastSeen_dtz
                    , null, null, null -- twitter, discord, telegram
                );
            ''')
            logging.debug(sql)
            with engine.begin() as con:
                res = con.execute(sql, {'address': whitelist.ergoAddress,'network': Network})
                resFindWallet = con.execute(sqlFindWallet, {'address': whitelist.ergoAddress}).fetchone()

        # found or created, get wallet address
        walletId = resFindWallet['id']
        # logging.warning(f'wallet id: {walletId}')

        # already whitelisted
        sqlCheckSignup = text(f'''
            select id 
            from "whitelist" 
            where "walletId" = :walletId 
                and "eventId" = :eventId
        ''')
        # logger.warning(f'check signup: {sqlCheckSignup}')
        resCheckSignup = None
        with engine.begin() as con:
            resCheckSignup = con.execute(sqlCheckSignup, {'walletId': walletId, 'eventId': eventId}).fetchone()
        logging.debug(f'check signup: {resCheckSignup}')

        # already signed up?
        if resCheckSignup is None:
            mt_id = None
            if whitelist.tpe == "cardano":
                mt = create_metadata(
                    get_db_ref(),
                    CreateOrUpdateCardanoMetadataWhitelistExt(kycApproval=whitelist.kycApproval, adaAddresses=whitelist.adaAddresses)
                )
                mt_id = mt.id
            sqlSignup = text(f'''
                insert into whitelist("walletId", "eventId", created_dtz, allowance_sigusd, spent_sigusd, "isAvailable", "lastAssemblerId", "lastAssemblerStatus", "isWhitelist", cardano_metadata_whitelist_ext_id)
	            values (
                      :walletId -- walletId
                    , :eventId -- eventId
                    , {dt.fromtimestamp(NOW).strftime(DATEFORMAT)!r} -- created_dtz
                    , :allowance_sigusd -- allowance_sigusd
                    , 0 -- spent_sigusd
                    , 1 -- isAvailable
                    , null, null -- lastAssemblerId, lastAssemblerStatus
                    , 1 -- isWhitelist
                    , :mt_id -- cardano_metadata_whitelist_ext_id
                );
            ''')
            with engine.begin() as con:
                con.execute(sqlSignup, {'walletId': walletId, 'eventId': eventId, 'allowance_sigusd': whitelist.sigValue, 'mt_id': mt_id})

            # use obfuscated identifier to prevent bots
            ipHash = get_md5_hash(request.client.host)
            sqlIpHash = text(f'''
                insert into "eventsIp" ("walletId", "eventId", "ipHash")
                values (
                      :walletId -- walletId
                    , :eventId -- eventId
                    , :ipHash -- ipHash
                )
            ''')
            # logger.warning(f'ip hash: {sqlIpHash}')
            with engine.begin() as con:
                resIpHash = con.execute(sqlIpHash, {'walletId': walletId, 'eventId': eventId, 'ipHash': ipHash})
            logging.debug(f'ip hash: {resIpHash}')

            # whitelist success
            return {'status': 'success', 'detail': f'added to whitelist: {whitelist.sigValue} SigUSD.'}

        # already whitelisted
        else:
            logging.warning(f'wallet, {walletId} already signed up for event, {eventName}')
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'wallet already signed up for this event')

    except Exception as e:
        logging.error(f'ERR:{myself()}: whitelist err, {e}', e)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to save whitelist request ({e})')


def checkEventConstraints(eventId: int, whitelist: Whitelist, db=next(get_db())):
    whitelistEvent = adjustWhitelistEarlyBird(
        get_whitelist_event_by_event_id(db, eventId)
    )
    additionalDetails = whitelistEvent.additionalDetails
    constraints = {"min_stake": 0}
    if "min_stake" in additionalDetails:
        constraints["min_stake"] = int(additionalDetails["min_stake"])
    address = whitelist.ergoAddress
    if (constraints["min_stake"] > 0):
        try:
            stakedRes = staked(AddressList(addresses=[address]))
            if stakedRes["totalStaked"] >= constraints['min_stake']:
                return (True, "ok")
            else:
                return (False, f"Not enough ergopad staked for this address. Min stake required is {constraints['min_stake']}.")
        except:
            return (False, "API failed. Could not validate if enough ergopad is staked.")
    return (True, "ok")


def backfill_usd_value(whitelist: Whitelist):
    if (whitelist.usdValue == None and whitelist.sigValue == None):
        whitelist.sigValue = 0
    if whitelist.usdValue != None:
        whitelist.sigValue = whitelist.usdValue
    return whitelist


def get_ada_address_hash(ada_addresses: t.List[str]):
    sorted_addresses = sorted(ada_addresses)
    return get_md5_hash(sorted_addresses.__str__())


def get_db_ref():
    return next(get_db())


def isStakerSnapshotWhitelist(eventId: int, db=next(get_db())):
    whitelistEvent = get_whitelist_event_by_event_id(db, eventId)
    additionalDetails = whitelistEvent.additionalDetails
    return "staker_snapshot_whitelist" in additionalDetails and additionalDetails["staker_snapshot_whitelist"]


def adjustWhitelistEarlyBird(event: WhitelistEvent):
    # check if early bird config is present
    if not event:
        return None
    if "early_bird" not in event.additionalDetails or event.additionalDetails["early_bird"] == None:
        return event

    # check if early bird period
    start_time = event.start_dtz.timestamp()
    current_time = time.time()
    early_bird__s = event.additionalDetails["early_bird"]["round_length__s"]
    if current_time <= start_time or start_time + early_bird__s <= current_time:
        return event

    # make edits to config
    event.additionalDetails["min_stake"] = event.additionalDetails["early_bird"]["min_stake"]
    event.title = event.title + " (Early Bird)"

    return event


@r.get("/summary/{eventName}", name="whitelist:summary")
def whitelistInfo(eventName,  current_user=Depends(get_current_active_user)):
    try:
        logging.debug(DATABASE)
        con = create_engine(DATABASE)
        sql = text(f"""
            select
                max(evt.name) as "name",
                wal.address,
                wht.cardano_metadata_whitelist_ext_id,
                max(wal.email) as email,
                max(wal."socialHandle") as social_handle,
                max(wal."socialPlatform") as social_platform,
                max(allowance_sigusd) as allowance_sigusd,
                ''::text as ip_hash,--eip."ipHash" as ip_hash,
                min(wht.created_dtz) as created_dtz
            from
                whitelist wht
                join wallets wal on wal.id = wht."walletId"
                join "eventsIp" eip on eip."eventId" = wht."eventId"
                join events evt on evt.id = wht."eventId"
                and eip."walletId" = wal.id
            where
                evt.name = :eventName
			group by wal.address, wht.cardano_metadata_whitelist_ext_id
            order by
                created_dtz;
        """)
        res = con.execute(sql, {'eventName': eventName}).fetchall()
        logging.debug(res)
        return {
            'status': 'success',
            'data': expand_cardano_metadata_whitelist_ext_id(res),
        }
    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid whitelist request ({e})')


def expand_cardano_metadata_whitelist_ext_id(data):
    return list(map(lambda row: expand_cardano_metadata_whitelist_ext_id_helper(row), data))


def expand_cardano_metadata_whitelist_ext_id_helper(row):
    res = row._asdict()
    if res["cardano_metadata_whitelist_ext_id"] == None:
        return res
    else:
        metadata = get_metadata(get_db_ref(), res["cardano_metadata_whitelist_ext_id"])
        if not metadata:
            return res
        res["ada_address_list"] = metadata.adaAddresses
        res["kyc_approval"] = metadata.kycApproval
    return res


##########################
## WHITELIST CMS CONFIG ##
##########################


@r.get(
    "/events",
    response_model_exclude_none=True,
    name="whitelist:all-events"
)
def whitelist_event_list(
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
def whitelist_event(
    projectName: str, 
    roundName: str,
    format: str = 'default',
    db=Depends(get_db),
):
    """
    Get event
    """
    try:
        event = get_whitelist_event_by_name(db, projectName, roundName)
        if format != 'adjust_early_bird':
            return event
        if type(event) == JSONResponse:
            return event
        return adjustWhitelistEarlyBird(event)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.post("/events", response_model_exclude_none=True, name="whitelist:create-event")
def whitelist_event_create(
    whitelist_event: CreateWhitelistEvent,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new event
    """
    try:
        return create_whitelist_event(db, whitelist_event)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/events/{id}", 
    response_model_exclude_none=True, 
    name="whitelist:edit-event"
)
def whitelist_event_edit(
    id: int,
    whitelist_event: CreateWhitelistEvent,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """
    Update existing event
    """
    try:
        return edit_whitelist_event(db, id, whitelist_event)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/events/{id}", 
    response_model_exclude_none=True, 
    name="whitelist:delete-event"
)
def whitelist_event_delete(
    id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete event
    """
    try:
        return delete_whitelist_event(db, id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')

# endregion ROUTES
