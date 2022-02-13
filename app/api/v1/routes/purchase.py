import requests, json, os
import math
import uuid

from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time, ctime
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeString
from config import Config, Network # api specific config
CFG = Config[Network]

purchase_router = r = APIRouter()

#region BLOCKHEADER
"""
Purchase API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: allow purchase/redeem tokens locked by ergopad scripts
Contributor(s): https://github.com/Luivatra

Notes:
=======
"""
#endregion BLOCKHEADER

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
buyerWallet = Wallet(CFG.buyerWallet) # simulate buyer / seed tokens
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

# purchase tokens
@r.post("/", name="blockchain:purchaseToken")
async def purchaseToken(tokenPurchase: TokenPurchase):
    # close route for now
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'use api/vesting')
    
    NOW = int(time())

    # early check
    eventName = 'presale-ergopad-202201p'
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
    logging.debug(sql)
    res = con.execute(sql).fetchone()
    logging.debug(res)

    # early 
    if NOW < int(res['start_dtz'].timestamp()):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'event not started')

    # late
    if NOW > int(res['end_dtz'].timestamp()):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'event ended')

    # full
    if int(res['spent_sigusd']) >= int(res['allowance_sigusd']):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'event purchase complete')

    # handle price exceptions
    event2Sigusd = res['eventConversion'] # .02 # strategic round .02 sigusd per token (50 strategic tokens per sigusd)
    tokenId = validCurrencies['ergopad'] #CFG.ergopadTokenId
    # priceOverride = 5.0
    price = 0.0
    try:
        sigusdCurrentPrice = await get_asset_current_price('sigusd') #Confusing naming, is this erg price in sigusd?
        if 'price' in sigusdCurrentPrice:
            price = sigusdCurrentPrice['price']
            if math.isnan(price): # NaN
                price = priceOverride
            if price < 1 or price > 1000: # OOS
                price = priceOverride

        if price == 0.0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid price: {price}')

    except Exception as e:
        logging.error(f'{myself()}: {e}')
        logging.error('invalid price found for sigusd')
        pass

    # handle token params
    sigusdDecimals = 0
    ergopadDecimals = 0
    try:
        tokenDecimals = getTokenInfo(validCurrencies['sigusd'])
        logging.debug(tokenDecimals)
        if 'decimals' in tokenDecimals:
            sigusdDecimals = int(tokenDecimals['decimals'])
        tokenDecimals = getTokenInfo(validCurrencies['ergopad'])
        if 'decimals' in tokenDecimals:
            ergopadDecimals = int(tokenDecimals['decimals'])

    except Exception as e:
        logging.error(f'{myself()}: {e}')
        logging.error('invalid decimals found for sigusd')
        pass

    logging.info(f'decimals for sigusd: {sigusdDecimals}, ergopad: {ergopadDecimals}')
    ergopadDecimals = 10**ergopadDecimals
    sigusdDecimals = 10**sigusdDecimals

    # handle purchase
    try:
        buyerWallet          = Wallet(tokenPurchase.wallet)
        amount               = tokenPurchase.amount #Purchase amount in SigUSD

        isToken              = True
        tokenName            = 'sigusd'
        if tokenPurchase.currency == 'erg':
            isToken          = False
            tokenName        = None

        nergsPerErg          = 1000000000
        txFee_nerg           = int(.001*nergsPerErg)

        # if sending sigusd, assert(isToken)=True
        tokenAmount          = int(amount/strategic2Sigusd)*ergopadDecimals
        coinAmount_nerg      = int(amount/price*nergsPerErg)
        sendAmount_nerg      = coinAmount_nerg+2*txFee_nerg
        if isToken:
            coinAmount_nerg  = txFee_nerg # min per box
            sendAmount_nerg  = 10000000 # coinAmount_nerg+txMin_nerg # +txFee_nerg

        logging.info(f'using {tokenName}, amount={tokenAmount/ergopadDecimals:.2f} at price={price} for {amount}sigusd')

        # check whitelist
        whitelist = {}
        try:
            con = create_engine(DATABASE)
            sql = f"""
                with evt as (
                    select id
                    from events
                    where name = {eventName!r}
                )
                select wht.id
                    , wal.id as walletId
                    , wal.address as wallet
                    , max(wht.allowance_sigusd) as allowance_sigusd
                    , max(wht.spent_sigusd) as spent_sigusd
                from whitelist wht
                    join evt on evt.id = wht."eventId"
                    join wallets wal on wal.id = wht."walletId"
                group by wal.address
            """
            res = con.execute(sql).fetchall()
            for r in res:
                whitelist[r['wallet']] = {
                    'id': r['id'],
                    'walletid': r['walletId'],
                    'eventId': r['eventId'],
                    'total': float(r['allowance_sigusd']),
                    'spent': float(r['spent_sigusd']),
                    'remaining': float(r['allowance_sigusd'])-float(r['spent_sigusd']),
                }
        
        except Exception as e:
            logging.error(f'ERR:{myself()}: reading whitelist ({e})')
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid whitelist amounts')

        # make sure buyer is whitelisted
        if buyerWallet.address not in whitelist:
            logging.debug(f'wallet not found in whitelist: {buyerWallet.address}')
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} invalid or not on whitelist')

        # make sure buyer remains under amount limit
        if amount > whitelist[buyerWallet.address]['remaining']:
            logging.debug(f"amount ({amount}) exceeds whitelist amount: {whitelist[buyerWallet.address]['remaining']}/{whitelist[buyerWallet.address]['total']}, including already spent amount: {whitelist[buyerWallet.address]['spent']}")
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} may only request up to {whitelist[buyerWallet.address]["total"]} sigusd')

        # 1 outbox per vesting period to lock spending until vesting complete
        logging.info(f'wallet: ok\nwhitelist: ok\nergs: {coinAmount_nerg} at price {price}')

        # pay ergopad for tokens with coins or tokens
        startWhen = {'erg': sendAmount_nerg}
        outBox = [{
                'address': nodeWallet.address, # nodeWallet.bs64(),
                'value': sendAmount_nerg # coinAmount_nerg
        }]
        if isToken:
            outBox[0]['assets'] = [{
                        'tokenId': validCurrencies[tokenName], # sigusd
                        'amount': int(amount*sigusdDecimals),
                    }]
            startWhen[validCurrencies[tokenName]] = int(amount*sigusdDecimals)

        logging.info(f'startWhen: {startWhen}')

        # create outputs for each vesting period; add remainder to final output, if exists
        r4 = '0e'+hex(len(bytearray.fromhex(buyerWallet.ergoTree())))[2:]+buyerWallet.ergoTree() # convert to bytearray
        outBox.append({
            'address': buyerWallet.address,
            'value': txFee_nerg,
            'registers': {
                'R4': r4
            },
            'assets': [{
                'tokenId': tokenId,
                'amount': int(tokenAmount) # full amount
            }]
        })

        logging.info(f'r4: {r4}')
        logging.info(f'wallets: {nodeWallet.address}, {buyerWallet.address}')
        logging.info(f"token: {tokenName}")

        # handle assembler
        params = {
            'nodeWallet': nodeWallet.address,
            'buyerWallet': buyerWallet.address,
            'timestamp': int(time()),
            'purchaseToken': b64encode(validCurrencies['ergopad'].encode('utf-8').hex().encode('utf-8')).decode('utf-8'),
            'purchaseTokenAmount': tokenAmount
        }
        logging.info(f'params: {params}')

        params = {
            'nodeWallet': nodeWallet.address,
            'buyerWallet': buyerWallet.address,
            'saleTokenId': b64encode(bytes.fromhex(validCurrencies['ergopad'])).decode('utf-8'),
            'saleTokenAmount': tokenAmount,
            'timestamp': int(time()),
        }
        if isToken:
            params['purchaseTokenId'] = b64encode(bytes.fromhex(validCurrencies['sigusd'])).decode('utf-8')
            params['purchaseTokenAmount'] = int(amount*sigusdDecimals)
        else:
            params['purchaseTokenId'] = ""
            params['purchaseTokenAmount'] = sendAmount_nerg # coinAmount_nerg
        logging.info(f'params: {params}')

        currencyAmount = params['purchaseTokenAmount']
        scPurchase = getErgoscript('directSale', params=params)
        logging.info(f'scPurchase: {scPurchase}')

        # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
        ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId=tokenId, nErgAmount=sendAmount_nerg, tokenAmount=tokenAmount)
        logging.info(f'build request')
        request = {
                'address': scPurchase,
                'returnTo': buyerWallet.address,
                'startWhen': startWhen,
                'txSpec': {
                        'requests': outBox,
                        'fee': txFee_nerg,
                        'inputs': ['$userIns']+list(ergopadTokenBoxes.keys()),
                        'dataInputs': [],
                },
        }

        # don't bonk if can't jsonify request
        try: logging.info(f'request: {json.dumps(request)}')
        except: pass

        # logging.info(f'build request: {request}')
        # logging.info(f'\n::REQUEST::::::::::::::::::\n{json.dumps(request)}\n::REQUEST::::::::::::::::::\n')

        # make async request to assembler
        res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)
        logging.debug(res)
        id = res.json()['id']
        fin = requests.get(f'{CFG.assembler}/result/{id}')
        logging.info({'status': 'success', 'fin': fin.json(), 'followId': id})

        # await handleAllowance()
        try:
            # save transaction (may be multiple)
            sql = f"""
                insert into purchases ("walletId", "eventId", "toAddress", "tokenId", "tokenAmount", "currency", "currencyAmount", "feeAmount")
                values (
                    {whitelist[buyerWallet.address]['walletId']!r},
                    {whitelist[buyerWallet.address]['eventId']!r},
                    {scPurchase!r},
                    {validCurrencies['ergopad']!r}, 
                    {tokenAmount!r},
                    {('erg', 'sigusd')[isToken]!r},
                    {currencyAmount!r},
                    txFee_nerg,
                )
            """
            res = con.execute(sql)

            # update summary
            sql = f"""
                update whitelist set spent_sigusd = {tokenPurchase.amount!r}
                where id = {whitelist[buyerWallet.address]['id']!r}
            """
            res = con.execute(sql)
        except:
            with open(BONKFILE, 'a') as f:
                f.write(f"--purchase ergopad for eventId {whitelist[buyerWallet.address]['eventId']}\n--{NOW}\n{sql};\n\n")
            pass

        logging.debug(f'::TOOK {time()-st:.2f}s')
        if isToken:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs and {amount} sigusd to {scPurchase}'
        else:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs to {scPurchase}'
        return({
                'status'        : 'success',
                'message'       : message,
                'total'         : sendAmount_nerg/nergsPerErg,
                'assembler'     : json.dumps(fin.json()),
                'smartContract' : scPurchase,
                'request'       : json.dumps(request),
        })

    except Exception as e:
        logging.error(f'ERR:{myself()}: building request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'building request')

@r.get("/allowance/{wallet}", name="blockchain:whitelist")
async def allowance(wallet:str, eventName:Optional[str]='presale-ergopad-202201wl'):
    NOW = int(time())

    try:
        con = create_engine(DATABASE)
        sql = f"""
            with evt as (
                select id, address
                from events
                where name = {eventName!r}
            )
            , wal as (
                select id
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'allowance remaining')

    logging.info(f'sigusd: 0 (not found)')
    return {'wallet': wallet, 'sigusd': 0.0, 'message': 'not found'}

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
