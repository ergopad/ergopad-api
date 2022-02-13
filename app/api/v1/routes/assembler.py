import logging
import requests

from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from fastapi import APIRouter, status
from config import Config, Network  # api specific config

assembler_router = r = APIRouter()

DEBUG = True
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

CFG = Config[Network]
DATABASE = CFG.connectionString
headers = {'Content-Type': 'application/json'}


@r.get("/return/{wallet}/{smartContract}", name="assembler:return")
async def assemblerReturn(wallet: str, smartContract: str):
    try:
        res = requests.get(f'{CFG.assembler}/return/{wallet}/{smartContract}')
        if res.status_code == 200:
            return JSONResponse(status_code=res.status_code, content=res.text)
        else:
            return JSONResponse(status_code=res.status_code, content=res.json())
    except:
        logging.debug(
            f'request failed for "wallet": {wallet}, "smartContract": {smartContract}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'network failure could not connect to assembler')

@r.get("/result/{assemblerId}")
async def assemblerStatus(assemblerId: str):
    try:
        res = requests.get(f'{CFG.assembler}/result/{assemblerId}')
        return JSONResponse(status_code=res.status_code, content=res.json())

    except:
        logging.debug(f'request failed for follow status: {assemblerId}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'failed for follow status')

@r.get("/status/{wallet}")
async def pendingStatus(wallet: str):
    try:
        con = create_engine(DATABASE)
        sql = f"""
            select distinct "assemblerStatus", "assemblerId"
            from purchases 
            where "walletAddress" = {wallet!r}
                and "assemblerStatus" not in ('success', 'timeout', 'ignore')
        """
        logging.debug(sql)
        res = con.execute(sql).fetchall()
        logging.debug(f'res: {res}')

        result = {}
        if res == None:
            JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'no wallet status results')
        else:
            for r in res:
                res = requests.get(f"{CFG.assembler}/result/{r['assemblerId']}")
                if res.ok:
                    result[r['assemblerId']] = res.json()['detail']
        return result

    except:
        logging.debug(f'request failed for wallet status: {wallet}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'failed for wallet status')
