from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from api.utils.wallet import Wallet
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time
from config import Config, Network # api specific config
from api.utils.logger import logger, myself, LEIF

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
        logger.debug(sql)
        res = con.execute(sql).fetchone()
        logger.debug(res)
        remainingSigusd = res['remaining_sigusd']
        logger.info(f'sigusd: {remainingSigusd} remaining')
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
        logger.error(f'ERR:{myself()}: allowance remaining ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: allowance remaining ({e})')
