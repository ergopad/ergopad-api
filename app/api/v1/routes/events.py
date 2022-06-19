import requests, json, os

from starlette.responses import JSONResponse 
from sqlalchemy import create_engine
from fastapi import APIRouter, Request, status #, Response
from time import time
from datetime import datetime as dt
from config import Config, Network # api specific config
from utils.logger import logger, myself

CFG = Config[Network]

events_router = r = APIRouter()

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

DATABASE = CFG.connectionString
DATEFORMAT = '%m/%d/%Y %H:%M'
NOW = int(time())

DEBUG = True
st = time() # stopwatch
#endregion INIT

@r.get("/summary/{eventName}")
def summary(eventName):
    try:
        headers = {'Content-Type': 'application/json', 'api_key': CFG.ergopadApiKey}

        startingTokenAmount = 20500000
        spentTokenAmount = 0
        res = requests.get(f'{CFG.node}/wallet/balances', headers=headers)
        if res.ok:
            try:
                balance = res.json()
                remainingTokenAmount = int(balance['assets']['d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413']/100)
                spentTokenAmount = startingTokenAmount - remainingTokenAmount
                return {
                    'event': eventName,
                    # 'id': res['id'],
                    'total presale (tokens)': f"\u046E\u262F{startingTokenAmount:,.2f}", # \u01A9\u0024
                    'spent presale (tokens)': f"\u046E\u262F{spentTokenAmount:,.2f}",
                    'remaining presale (tokens)': f"\u046E\u262F{remainingTokenAmount:,.2f}",
                }
            except:
                pass

        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid events request ({res.text})')

    except Exception as e:
        logger.error(f'ERR:{myself()}: events info {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: events info {e}')

@r.get("/info/{eventName}")
def events(eventName):
    # return {'hello': 'world'}
    try:
        if eventName != '_':
            where = f"where name = {eventName!r}"
        else:
            where = ''
        con = create_engine(DATABASE)
        sql = f"""
            select id, name, description, total_sigusd, buffer_sigusd, "walletId", "individualCap", "vestedTokenId", "vestingPeriods", "vestingPeriodDuration", "vestingPeriodType", "tokenPrice", "isWhitelist", start_dtz, end_dtz
            from events
            {where}
        """
        # logger.debug(sql)
        res = con.execute(sql)
        # logger.debug(res)
        events = []
        for r in res:
            events.append({
                "id": r['id'],
                "name": r['name'],
                "description": r['description'],
                "total_sigusd": r['total_sigusd'],
                "buffer_sigusd": r['buffer_sigusd'],
                "walletId": r['walletId'],
                "individualCap": r['individualCap'],
                "vestedTokenId": r['vestedTokenId'],
                "vestingPeriods": r['vestingPeriods'],
                "vestingPeriodDuration": r['vestingPeriodDuration'],
                "vestingPeriodType": r['vestingPeriodType'],
                "tokenPrice": r['tokenPrice'],
                "isWhitelist": r['isWhitelist'],
                "start_dtz": r['start_dtz'],
                "end_dtz": r['end_dtz'],
            })
        return events

    except:
        logger.error(f'ERR:{myself()}: events info {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: events info {e}')
