from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time, ctime
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.util import encodeLong, encodeString
from config import Config, Network # api specific config

CFG = Config[Network]

purchase_router = r = APIRouter()

#region INIT
DEBUG = CFG.debug
DATABASE = CFG.connectionString
DATEFORMAT = '%m/%d/%Y %H:%M'
BONKFILE = "bonk.txt" # dump missed sql queries

class TokenPurchase(BaseModel):
    wallet: str
    amount: float
    isToken: Optional[bool] = True
    currency: Optional[str] = 'sigusd'

nodeWallet  = Wallet(CFG.ergopadWallet) # contains ergopad tokens (xerg10M)
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

@r.get("/allowance/{wallet}", name="blockchain:whitelist")
async def allowance(wallet:str, eventName:Optional[str]='presale-ergopad-202201wl'):
    NOW = int(time())

    try:
        con = create_engine(DATABASE)
        sql = f"""
            with evt as (
                select id
                from events
                where name = {eventName!r}
            )
            , wal as (
                select id, address
                from wallets
                where address = {wallet!r}
            )
            , pur as (
                select "walletAddress", sum(coalesce("sigusdAmount", 0.0)) as "sigusdAmount"
                from purchases
                where "walletAddress" = {wallet!r}
                    and "assemblerStatus" = 'success'
                group by "walletAddress"
            )
            select coalesce(sum(coalesce(allowance_sigusd-spent_sigusd, 0.0)), 0.0) as remaining_sigusd
                , coalesce(max(pur."sigusdAmount"), 0.0) as success_sigusd
            from whitelist wht
                join evt on evt.id = wht."eventId"
                join wal on wal.id = wht."walletId"        
                left outer join pur on pur."walletAddress" = wal.address
            where wht."isWhitelist" = 1    
        """
        logging.debug(sql)
        res = con.execute(sql).fetchone()
        logging.debug(res)
        remainingSigusd = res['remaining_sigusd']
        logging.info(f'sigusd: {remainingSigusd} remaining')
        if remainingSigusd == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid wallet or allowance; wallet may not exist or remaining value is non-numeric')
        else:
            return {
                'wallet': wallet, 
                'remaining (sigusd)': res['remaining_sigusd'], 
                'successes (sigusd)': res['success_sigusd'], 
                'sigusd': res['remaining_sigusd'], 
            }

    except Exception as e:
        logging.error(f'ERR:{myself()}: allowance remaining ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: allowance remaining ({e})')

    logging.info(f'sigusd: 0 (not found)')
    return {'wallet': wallet, 'sigusd': 0.0, 'message': 'not found'}

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
