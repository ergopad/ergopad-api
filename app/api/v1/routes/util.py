import requests

from starlette.responses import JSONResponse
from fastapi import APIRouter, Request, Depends, status
from typing import Optional
from pydantic import BaseModel
from smtplib import SMTP
from config import Config, Network  # api specific config
from core.auth import get_current_active_superuser
from cache.cache import cache
from api.utils.logger import logger, myself, LEIF

CFG = Config[Network]

util_router = r = APIRouter()

# region INIT
DEBUG = CFG.debug
headers = {'Content-Type': 'application/json'}
# endregion INIT

# region CLASSES
class Ergoscript(BaseModel):
    script: str  # wallet

    class Config:
        schema_extra = {
            "example": {
                'script': '{ 1 == 1 }',
            }
        }
# endregion CLASSES

@r.post("/compileErgoscript", name="blockchain:sendPayment")
def compileErgoscript(ergoscript: Ergoscript):
    try:
        script = {'source': ergoscript.script}
        p2s = requests.post(f'{CFG.node}/script/p2sAddress', headers=dict(
            headers, **{'api_key': CFG.ergopadApiKey}), timeout=2, json=script)
        if p2s.ok:
            return p2s.json()['address']
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid ergoscript:\n{ergoscript.script}')

    except Exception as e:
        logger..error(f'ERR:{myself()}: unable to compile ergoscript ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to compile ergoscript ({e})')

class InvalidateCacheRequest(BaseModel):
    key: str

@r.post("/forceInvalidateCache", name="cache:invalidate")
def forceInvalidateCache(req: InvalidateCacheRequest, current_user=Depends(get_current_active_superuser)):
    return {'status': 'success', 'detail': cache.invalidate(req.key)}
