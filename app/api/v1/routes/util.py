import inspect
import logging
import requests
import ssl
import typing as t
from unicodedata import normalize

from starlette.responses import JSONResponse
from fastapi import APIRouter, Request, Depends, status
from typing import Optional
from pydantic import BaseModel
from smtplib import SMTP
from config import Config, Network  # api specific config
from core.auth import get_current_active_superuser

from cache.cache import cache

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

class Email(BaseModel):
    to: str
    # sender: str
    subject: Optional[str] = 'ErgoPad'
    body: Optional[str] = ''

    class Config:
        schema_extra = {
            'to': 'hello@world.com',
            'subject': 'greetings',
            'body': 'this is a message.'
        }
# endregion CLASSES

# region LOGGING
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

def myself(): return inspect.stack()[1][3]
# endregion LOGGING

@r.post("/email")
async def email(email: Email, request: Request):
    try:
        # validate referer
        logging.debug(request.headers)
        referer = request.headers.get('referer') or ''
        if 'https://www.ergopad.io/' not in referer:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to send email from this location')

        usr = CFG.emailUsername
        pwd = CFG.emailPassword
        svr = CFG.emailSMTP
        frm = CFG.emailFrom
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)

        # create connection
        logging.info(f'creating connection for: {svr} as {usr}')
        con = SMTP(svr, 587)
        res = con.ehlo()
        res = con.starttls(context=ctx)
        if res[0] == 220: logging.info('starttls success')
        else: logging.error(res)
        res = con.ehlo()
        res = con.login(usr, pwd)
        if res[0] == 235: logging.info('login success')
        else: logging.error(res)

        msg = normalize('NFKD', f"""From: {frm}\nTo: {email.to}\nSubject: {email.subject}\n\n{email.body}""")
        res = con.sendmail(frm, email.to, msg)
        if res == {}: logging.info('message sent')
        else: logging.error(res)

        return {'status': 'success', 'detail': f'email sent to {email.to}'}

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: ({e})')

@r.post("/compileErgoscript", name="blockchain:sendPayment")
async def compileErgoscript(ergoscript: Ergoscript):
    try:
        script = {'source': ergoscript.script}
        p2s = requests.post(f'{CFG.node}/script/p2sAddress', headers=dict(
            headers, **{'api_key': CFG.ergopadApiKey}), timeout=2, json=script)
        if p2s.ok:
            return p2s.json()['address']
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid ergoscript:\n{ergoscript.script}')

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to compile ergoscript ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to compile ergoscript ({e})')


class InvalidateCacheRequest(BaseModel):
    keys: t.List[str]

@r.post("/forceInvalidateCache", name="cache:invalidate")
def forceInvalidateCache(req: InvalidateCacheRequest, current_user = Depends(get_current_active_superuser)):
    try:
        invalidation_count = sum(map(lambda key : cache.invalidate(key), req.keys))
        return {'status': 'success', 'invalidation_count': invalidation_count}
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to invalidate cache ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'({str(e)})')
