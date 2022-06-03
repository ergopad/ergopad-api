import json, ssl

from starlette.responses import JSONResponse
from fastapi import APIRouter, Request, Depends, status
from typing import Optional
from pydantic import BaseModel
from smtplib import SMTP
from config import Config, Network  # api specific config
from core.auth import get_current_active_superuser
from cache.cache import cache
from api.utils.aioreq import Req
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

@r.post("/email")
async def email(email: Email, request: Request):
    try:
        # validate referer
        logger.debug(request.headers)
        validEmailApply = CFG.validEmailApply
        referer = request.headers.get('referer') or ''
        validateMe = request.headers.get('validate_me') or ''
        isValidReferer = False
        if referer in validEmailApply: isValidReferer = True
        if '54.214.59.165' in referer: isValidReferer = True
        if validateMe == CFG.validateMe: isValidReferer = True
        if not isValidReferer:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to send email from this location')

        usr = CFG.emailUsername
        pwd = CFG.emailPassword
        svr = CFG.emailSMTP
        frm = CFG.emailFrom
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)

        # create connection
        logger.info(f'creating connection for: {svr} as {usr}')
        con = SMTP(svr, 587)
        res = con.ehlo()
        res = con.starttls(context=ctx)
        if res[0] == 220: logger.info('starttls success')
        else: logger.error(res)
        res = con.ehlo()
        res = con.login(usr, pwd)
        if res[0] == 235: logger.info('login success')
        else: logger.error(res)

        msg = f"""From: {frm}\nTo: {email.to}\nSubject: {email.subject}\n\n{email.body}"""
        res = con.sendmail(frm, email.to, msg) # con.sendmail(frm, 'erickson.winter@gmail.com', msg)
        if res == {}: logger.info('message sent')
        else: logger.error(res)

        return {'status': 'success', 'detail': f'email sent to {email.to}'}

    except Exception as e:
        logger.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: ({e})')

@r.post("/compileErgoscript", name="blockchain:sendPayment")
async def compileErgoscript(ergoscript: Ergoscript):
    try:
        data = {'source': ergoscript.script}
        # p2s = requests.post(f'{CFG.node}/script/p2sAddress', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), timeout=2, json=script)
        async with Req() as r:
            p2s = await r.post(f'{CFG.node}/script/p2sAddress', headers=headers, data=json.dumps(data))
        if p2s.ok:
            return p2s.json()['address']
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid ergoscript:\n{ergoscript.script}')

    except Exception as e:
        logger.error(f'ERR:{myself()}: unable to compile ergoscript ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to compile ergoscript ({e})')

class InvalidateCacheRequest(BaseModel):
    key: str

@r.post("/forceInvalidateCache", name="cache:invalidate")
def forceInvalidateCache(req: InvalidateCacheRequest, current_user=Depends(get_current_active_superuser)):
    return {'status': 'success', 'detail': cache.invalidate(req.key)}
