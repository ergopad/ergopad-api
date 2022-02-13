import requests, json, os
import ssl
import pandas as pd

from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from fastapi import APIRouter, Response, status #, Request
from fastapi.encoders import jsonable_encoder
from typing import Optional
from pydantic import BaseModel
from time import time
from smtplib import SMTP
from config import Config, Network # api specific config
CFG = Config[Network]

util_router = r = APIRouter()

#region BLOCKHEADER
"""
Utilities
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211129
Purpose: Common support requests

Notes:
"""
#endregion BLOCKHEADER

#region INIT
DEBUG   = CFG.debug
headers = {'Content-Type': 'application/json'}

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

class Ergoscript(BaseModel):
    script: str # wallet

    class Config:
        schema_extra = {
            "example": {
                'script': '{ 1 == 1 }',
            }
        }
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

@r.post("/email")
async def email(email: Email):
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
    
    msg = f"""From: {frm}\nTo: {email.to}\nSubject: {email.subject}\n\n{email.body}"""
    res = con.sendmail(frm, email.to, msg) # con.sendmail(frm, 'erickson.winter@gmail.com', msg)
    if res == {}: logging.info('message sent')
    else: logging.error(res)
    
    return {'status': 'success', 'detail': f'email sent to {email.to}'}

@r.post("/compileErgoscript", name="blockchain:sendPayment")
def compileErgoscript(ergoscript: Ergoscript):
    try:
        script = {'source': ergoscript.script}
        p2s = requests.post(f'{CFG.node}/script/p2sAddress', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), timeout=2, json=script)
        if p2s.ok:
            return p2s.json()['address']
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid ergoscript:\n{ergoscript.script}')

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to send payment ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to compile ergoscript')

# TEST - send payment from test wallet
@r.get("/sendPayment/{address}/{nergs}/{tokens}", name="blockchain:sendPayment")
def sendPayment(address, nergs, tokens):
    # TODO: require login/password or something; disable in PROD
    try:
        if not DEBUG:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=f'not found')
            # return {'status': 'fail', 'detail': f'only available in DEBUG mode'}

        sendMe = ''
        isWalletLocked = False

        # !! add in check for wallet lock, and unlock/relock if needed
        lck = requests.get(f'http://ergonode2:9052/wallet/status', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'})
        logging.info(lck.content)
        if lck.ok:
                if lck.json()['isUnlocked'] == False:
                        ulk = requests.post(f'http://ergonode2:9052/wallet/unlock', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json={'pass': 'crowdvacationancientamber'})
                        logging.info(ulk.content)
                        if ulk.ok: isWalletLocked = False
                        else: isWalletLocked = True
                else: isWalletLocked = True
        else: isWalletLocked = True

        # unlock wallet
        if isWalletLocked:
                logging.info('unlock wallet')

        # send nergs to address/smartContract from the buyer wallet
        # for testing, address/smartContract is 1==1, which anyone could fulfill
        sendMe = [{
                'address': address,
                'value': int(nergs),
                'assets': [{"tokenId": validCurrencies['seedsale'], "amount": tokens}],
                # 'assets': [],

        }]
        pay = requests.post(f'http://ergonode2:9052/wallet/payment/send', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json=sendMe)

        # relock wallet
        if not isWalletLocked:
                logging.info('relock wallet')

        return {'status': 'success', 'detail': f'payment: {pay.json()}'}

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to send payment ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to send payment')

