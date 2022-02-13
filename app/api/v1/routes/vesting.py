import requests, json, os
import math
from sqlalchemy import create_engine
from starlette.responses import JSONResponse 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time
from datetime import date, datetime, timezone
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeString
import uuid
from hashlib import blake2b
from api.v1.routes.blockchain import getTokenInfo, getErgoscript, getBoxesWithUnspentTokens

vesting_router = r = APIRouter()

CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

nergsPerErg        = 1000000000
headers            = {'Content-Type': 'application/json'}

duration_ms = {
    'month': 365*24*60*60*1000/12,
    'week': 7*24*60*60*1000,
    'day': 24*60*60*1000,
    'minute': 60*1000
}

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

class Vestment(BaseModel):
    wallet: str
    vestingAmount: float
    vestingScenario: str

class VestmentScenario(BaseModel):
    currency: str
    currencyPrice: Optional[float]
    vestedToken: str
    vestedTokenPrice: float
    vestingPeriods: float
    periodDuration: float
    periodType: str
    vestingBegin: float
    enabled: bool

def getScenario(scenarioName: str):
    if scenarioName == "seedsale":
        return VestmentScenario(
            currency = "seedsale",
            currencyPrice = 0.011,
            vestedToken = "ergopad",
            vestedTokenPrice = 0.011,
            vestingPeriods = 9,
            periodDuration = 1,
            periodType = "month",
            enabled = True,
            vestingBegin = datetime(2022,1,26,21,tzinfo=timezone.utc).timestamp()*1000-duration_ms['month'] #The first tokens should be released on jan 26th
        )
    if scenarioName == "strategic_sale":
        return VestmentScenario(
            currency = "strategic_sale",
            currencyPrice = 0.02,
            vestedToken = "ergopad",
            vestedTokenPrice = 0.02,
            vestingPeriods = 6,
            periodDuration = 1,
            periodType = "month",
            enabled = True,
            vestingBegin = datetime(2022,1,26,21,tzinfo=timezone.utc).timestamp()*1000-duration_ms['month'] #The first tokens should be released on jan 26th
        )
    if scenarioName == "presale_ergo":
        return VestmentScenario(
            currency = "ergo",
            currencyPrice = None,
            vestedToken = "ergopad",
            vestedTokenPrice = 0.03,
            vestingPeriods = 3,
            periodDuration = 1,
            periodType = "month",
            enabled = True,
            vestingBegin = datetime(2022,1,26,21,tzinfo=timezone.utc).timestamp()*1000-duration_ms['month'] #The first tokens should be released on jan 26th
        )
    if scenarioName == "presale_sigusd":
        return VestmentScenario(
            currency = "sigusd",
            currencyPrice = 1.0,
            vestedToken = "ergopad",
            vestedTokenPrice = 0.03,
            vestingPeriods = 3,
            periodDuration = 1,
            periodType = "month",
            enabled = True,
            vestingBegin = datetime(2022,1,26,21,tzinfo=timezone.utc).timestamp()*1000-duration_ms['month'] #The first tokens should be released on jan 26th
        )
    return

# purchase tokens
@r.post("/vest/", name="vesting:vestToken")
async def vestToken(vestment: Vestment): 
    st = int(time())
    vs = getScenario(vestment.vestingScenario)
    if vs is None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unknown vesting scenario')
    if not vs.enabled:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Disabled vesting scenario')

    if vs.currencyPrice is None:
        vs.currencyPrice = (await get_asset_current_price(vs.currency))["price"]
    if vs.vestedTokenPrice is None:
        vs.vestedTokenPrice = (await get_asset_current_price(vs.vestedToken))["price"]
    isToken = vs.currency != "ergo"
    logging.info(f'Price info: {vs.currency} = {vs.currencyPrice} USD, {vs.vestedToken} = {vs.vestedTokenPrice}')

    # for presale, verify on whitelist and that allowance is respected
    presale = {}
    if vestment.vestingScenario == "presale_sigusd" or vestment.vestingScenario == "presale_ergo":
        con = create_engine(DATABASE)
        sql = f"""
            with wal as (
                select id, address, email, "chatHandle", "chatPlatform"
                from wallets
                where address = {vestment.wallet!r}
            )
            , evt as (
                select id
                from events 
                where name = 'presale-ergopad-202201wl'
            )
            select 
                wht.id as "whitelistId", wht.allowance_sigusd, wht.spent_sigusd -- , wht.created_dtz
                , wal.id as "walletId" -- , wal.address, wal.email, wal."chatHandle", wal."chatPlatform"
                , evt.id as "eventId"
            from whitelist wht 
                join wal on wal.id = wht."walletId" 
                join evt on evt.id = wht."eventId" 
            
        """
        logging.debug(sql)
        res = con.execute(sql).fetchone()
        logging.debug(f'res: {res}')

        presale['allowance_sigusd'] = res['allowance_sigusd']
        presale['spent_sigusd'] = res['spent_sigusd']
        presale['remaining_sigusd'] = res['allowance_sigusd'] - res['spent_sigusd']
        presale['walletId'] = res['walletId']
        presale['eventId'] = res['eventId']
        presale['whitelistId'] = res['whitelistId']

        # missing legit response from whitelist
        if res == None or len(res) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'status': 'error', 'message': f'presale info not found.'}

        # allowance is fully spent
        if res['spent_sigusd'] >= res['allowance_sigusd']:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'status': 'error', 'message': f'purchase limit reached.'}

    # handle token params
    currencyDecimals = None
    vestedTokenDecimals = None
    try:
        if isToken:
            tokenDecimals = getTokenInfo(CFG.validCurrencies[vs.currency])
            logging.debug(tokenDecimals)
            if 'decimals' in tokenDecimals:
                currencyDecimals = int(tokenDecimals['decimals'])
            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not retrieve token decimals')
        else:
            currencyDecimals = 9
        tokenDecimals = getTokenInfo(CFG.validCurrencies[vs.vestedToken])
        if 'decimals' in tokenDecimals:
            vestedTokenDecimals = int(tokenDecimals['decimals'])
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not retrieve token decimals')
    except Exception as e:
        logging.error(f'{myself()}: {e}')
        logging.error('invalid decimals found for sigusd')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Invalid token decimals')

    logging.info(f'decimals for currency: {currencyDecimals}, vestedToken: {vestedTokenDecimals}')
    vestedTokenDecimals = 10**vestedTokenDecimals
    currencyDecimals = 10**currencyDecimals

    nodeWalletAddress = CFG.nodeWallet
    try:
        logging.info(CFG.nodeWallet)
        buyerWallet        = Wallet(vestment.wallet)
        nodeWallet         = Wallet(nodeWalletAddress)
        amountInUSD        = vestment.vestingAmount*vs.vestedTokenPrice
        
        vestingDuration_ms = duration_ms[vs.periodType]*vs.periodDuration
        vestingBegin_ms    = vs.vestingBegin

        txFee_nerg         = int(.001*nergsPerErg)
        tokenAmount        = vestment.vestingAmount*vestedTokenDecimals
        currencyAmount     = amountInUSD/vs.currencyPrice
        coinAmount_nerg    = int(.01*nergsPerErg)
        if vs.currency == "ergo":
            coinAmount_nerg = int(currencyAmount*nergsPerErg)
        sendAmount_nerg    = coinAmount_nerg

        logging.info(f'using {vs.currency}, amount={vestment.vestingAmount:.2f} at price={vs.vestedTokenPrice} for {amountInUSD}sigusd')

        # pay ergopad for tokens with coins or tokens
        startWhen = {'erg': sendAmount_nerg}
        outBox = [{
            'address': nodeWallet.address, 
            'value': sendAmount_nerg 
        }]
        if isToken:
            outBox[0]['assets'] = [{
                'tokenId': CFG.validCurrencies[vs.currency], # sigusd
                'amount': int(currencyAmount*currencyDecimals),
            }]
            startWhen[CFG.validCurrencies[vs.currency]] = int(currencyAmount*currencyDecimals)
    
        logging.info(f'startWhen: {startWhen}')
        scVesting = getErgoscript('vesting2', params={})

        # create outputs for each vesting period; add remainder to final output, if exists
        r4 = encodeString(buyerWallet.ergoTree()) # convert to bytearray
        r5 = encodeLong(int(vestingDuration_ms))
        r6 = encodeLong(int(tokenAmount/vs.vestingPeriods))
        r7 = encodeLong(int(vestingBegin_ms))
        r8 = encodeLong(int(tokenAmount))
        r9 = encodeString(uuid.uuid4().hex)
        outBox.append({
            'address': scVesting,
            'value': txFee_nerg,
            'registers': {
                'R4': r4,
                'R5': r5,
                'R6': r6,
                'R7': r7,
                'R8': r8,
                'R9': r9
            },
            'assets': [{ 
                'tokenId': CFG.validCurrencies[vs.vestedToken],
                'amount': tokenAmount
            }]
        })
        currencyID = CFG.validCurrencies[vs.currency] if isToken else ""
        params = {
            'nodeWallet': nodeWallet.address,
            'buyerWallet': buyerWallet.address,
            'vestingErgoTree': b64encode(bytes.fromhex(Wallet(scVesting).ergoTree()[2:])).decode('utf-8'),
            'saleToken': b64encode(bytes.fromhex(CFG.validCurrencies[vs.vestedToken])).decode('utf-8'),
            'saleTokenAmount': int(tokenAmount),
            'timestamp': int(time()),
            'purchaseToken': b64encode(bytes.fromhex(currencyID)).decode('utf-8'),
            'purchaseTokenAmount': int(currencyAmount*currencyDecimals),
            'redeemPeriod': int(vestingDuration_ms),
            'redeemAmount': int(tokenAmount/vs.vestingPeriods),
            'vestingStart': int(vestingBegin_ms)
        }
        logging.info(params)
        scPurchase = getErgoscript('vesting1', params=params)
        # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
        if presale == {}:
            ergopadTokenBoxes = getUnspentExchange()
        ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId=CFG.validCurrencies[vs.vestedToken], nErgAmount=txFee_nerg*3, tokenAmount=tokenAmount)
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
        logging.debug(res.content)
        assemblerId = res.json()['id']
        fin = requests.get(f'{CFG.assembler}/result/{assemblerId}')
        logging.info({'status': 'success', 'fin': fin.json(), 'followId': assemblerId})

        # track purchases
        con = create_engine(DATABASE)
        sql = f"""
            insert into purchases ("walletAddress", "eventName", "toAddress", "tokenId", "tokenAmount", "currency", "currencyAmount", "feeAmount", "assemblerId")
            values (
                {buyerWallet.address!r}
                , 'presale-ergopad-202201wl'
                , {scPurchase!r}
                , {CFG.validCurrencies[vs.vestedToken]!r}
                , {tokenAmount!r}
                , {vs.currency!r}
                , {(sendAmount_nerg/nergsPerErg, currencyAmount)[isToken]!r}
                , {txFee_nerg!r}
                , {assemblerId!r}
            )
        """
        logging.debug(f'SQL::PURCHASES::\n{sql}')
        res = con.execute(sql)
        logging.debug(res)

        # update if presale/whitelist
        if presale != {}:
            try:
                sql = f"""
                    update whitelist 
                    set spent_sigusd = coalesce(spent_sigusd, 0.0)+{amountInUSD!r}
                    where id = {presale['whitelistId']!r}
                """
                logging.debug(sql)
                # res = con.execute(sql)
            except:
                pass

        logging.debug(f'::TOOK {time()-st:.2f}s')
        if isToken:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs and {currencyAmount} {vs.currency} to {scPurchase}'
        else:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs to {scPurchase}'
        return({
            'status'        : 'success', 
            'message'       : message,
            'total'         : sendAmount_nerg/nergsPerErg,
            # 'coins'         : coinAmount_nerg/nergsPerErg,
            # 'boxes'         : txBoxTotal_nerg/nergsPerErg,
            # 'fees'          : txFee_nerg/nergsPerErg,
            'currencyAmount': currencyAmount,
            'currency'      : vs.currency,
            'assembler'     : json.dumps(fin.json()),
            'smartContract' : scPurchase, 
            'request'       : json.dumps(request),
        })

    except Exception as e:
        logging.error(f'ERR:{myself()}: building request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'building request')

# redeem/disburse tokens after lock
@r.get("/redeem/{address}", name="vesting:redeem")
def redeemToken(address:str, numBoxes:Optional[int]=200):

    txFee_nerg = CFG.txFee
    txBoxTotal_nerg = 0
    scPurchase = getErgoscript('alwaysTrue', {})
    outBoxes = []
    inBoxes = []
    currentTime = requests.get(f'{CFG.ergopadNode}/blocks/lastHeaders/1', headers=dict(headers),timeout=2).json()[0]['timestamp']
    offset = 0
    res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers), timeout=2) #This needs to be put in a loop in case of more than 500 boxes
    while res.ok:
        rJson = res.json()
        logging.info(rJson['total'])
        for box in rJson['items']:
            if len(inBoxes) >= numBoxes:
                break
            redeemPeriod = int(box['additionalRegisters']['R5']['renderedValue'])
            redeemAmount = int(box['additionalRegisters']['R6']['renderedValue'])
            vestingStart = int(box['additionalRegisters']['R7']['renderedValue'])
            totalVested = int(box['additionalRegisters']['R8']['renderedValue'])
            timeVested = int(currentTime - vestingStart)
            periods = int(timeVested/redeemPeriod)
            redeemed = totalVested - box['assets'][0]['amount']
            totalRedeemable = periods * redeemAmount
            redeemableTokens = totalVested - redeemed if (totalVested-totalRedeemable) < redeemAmount else totalRedeemable - redeemed
            if redeemableTokens > 0:
                nodeRes = requests.get(f"{CFG.ergopadNode}/utils/ergoTreeToAddress/{box['additionalRegisters']['R4']['renderedValue']}").json()
                buyerAddress = nodeRes['address']
                if (totalVested-(redeemableTokens+redeemed))>0:
                    outBox = {
                        'address': box['address'],
                        'value': box['value'],
                        'registers': {
                            'R4': box['additionalRegisters']['R4']['serializedValue'],
                            'R5': box['additionalRegisters']['R5']['serializedValue'],
                            'R6': box['additionalRegisters']['R6']['serializedValue'],
                            'R7': box['additionalRegisters']['R7']['serializedValue'],
                            'R8': box['additionalRegisters']['R8']['serializedValue'],
                            'R9': box['additionalRegisters']['R9']['serializedValue']
                        },
                        'assets': [{
                            'tokenId': box['assets'][0]['tokenId'],
                            'amount': (totalVested-(redeemableTokens+redeemed))
                        }]
                    }
                    txBoxTotal_nerg += box['value']
                    outBoxes.append(outBox)
                outBox = {
                    'address': str(buyerAddress),
                    'value': txFee_nerg,
                    'assets': [{
                        'tokenId': box['assets'][0]['tokenId'],
                        'amount': redeemableTokens
                }],
                'registers': {
                    'R4': box['additionalRegisters']['R9']['serializedValue']
                }
                }
                outBoxes.append(outBox)
                txBoxTotal_nerg += txFee_nerg
                inBoxes.append(box['boxId'])

        if len(res.json()['items']) == 500 and len(inBoxes) < 200:
            offset += 500
            res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers), timeout=2)
        else:
            break

    # redeem
    result = ""
    if len(outBoxes) > 0:
        inBoxesRaw = []
        txFee = max(txFee_nerg,(len(outBoxes)+len(inBoxes))*100000)
        ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId="", nErgAmount=txBoxTotal_nerg+txFee, tokenAmount=0)
        for box in inBoxes+list(ergopadTokenBoxes.keys()):
            res = requests.get(f'{CFG.ergopadNode}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
            if res.ok:
                inBoxesRaw.append(res.json()['bytes'])
        request = {
                'requests': outBoxes,
                'fee': txFee,          
                'inputsRaw': inBoxesRaw
            }

        # make async request to assembler
        # logging.info(request); exit(); # !! testing
        logging.debug(request)
        res = requests.post(f'{CFG.ergopadNode}/wallet/transaction/send', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), json=request)   
        logging.debug(res)
        result = res.content
    try:
        return({
            'status': 'success',
            'inboxes': len(inBoxes),
            'outboxes': len(outBoxes),
            'result': result,
        })
    
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to redeem ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to redeem')

# find vesting/vested tokens
@r.get("/vested/{wallet}", name="vesting:findVestedTokens")
def findVestingTokens(wallet:str):
  try:
    #tokenId     = CFG.ergopadTokenId
    total       = 0
    result = {}
    userWallet = Wallet(wallet)
    userErgoTree = userWallet.ergoTree()
    address = CFG.vestingContract
    offset = 0
    res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers), timeout=2)
    while res.ok: 
        # returns array of dicts
        for box in res.json()["items"]:
            if box["additionalRegisters"]["R4"]["renderedValue"] == userErgoTree:
                tokenId = box["assets"][0]["tokenId"]
                if tokenId not in result:
                    result[tokenId] = {}
                    result[tokenId]['name'] = box["assets"][0]["name"]
                    result[tokenId]['totalVested'] = 0.0
                    result[tokenId]['outstanding'] = {}
                tokenDecimals = 10**box["assets"][0]["decimals"]
                initialVestedAmount = int(box["additionalRegisters"]["R8"]["renderedValue"])/tokenDecimals
                nextRedeemAmount = int(box["additionalRegisters"]["R6"]["renderedValue"])/tokenDecimals
                remainingVested = int(box["assets"][0]["amount"])/tokenDecimals
                result[tokenId]['totalVested'] += remainingVested
                nextRedeemTimestamp = (((initialVestedAmount-remainingVested)/nextRedeemAmount+1)*int(box["additionalRegisters"]["R5"]["renderedValue"])+int(box["additionalRegisters"]["R7"]["renderedValue"]))/1000.0
                nextRedeemDate = date.fromtimestamp(nextRedeemTimestamp)
                while remainingVested > 0:
                    if nextRedeemDate not in result[tokenId]['outstanding']:
                        result[tokenId]['outstanding'][nextRedeemDate] = {}
                        result[tokenId]['outstanding'][nextRedeemDate]['amount'] = 0.0
                    redeemAmount = nextRedeemAmount if remainingVested >= 2*nextRedeemAmount else remainingVested
                    result[tokenId]['outstanding'][nextRedeemDate]['amount'] += round(redeemAmount,int(box["assets"][0]["decimals"]))
                    remainingVested -= redeemAmount
                    nextRedeemTimestamp += int(box["additionalRegisters"]["R5"]["renderedValue"])/1000.0
                    nextRedeemDate = date.fromtimestamp(nextRedeemTimestamp)
        if len(res.json()['items']) == 500:
            offset += 500
            res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={0}&limit=500', headers=dict(headers), timeout=2)
        else:
            break
    
    resJson = []
    for key in result.keys():
        tokenResult = {}
        value = result[key]
        tokenResult['tokenId'] = key
        tokenResult['name'] = value['name']
        tokenResult['totalVested'] = value['totalVested']
        tokenResult['outstanding'] = []
        for redeemDate in sorted(value['outstanding'].keys()):
            tokenResult['outstanding'].append({'date': redeemDate, 'amount': value['outstanding'][redeemDate]['amount']})
        resJson.append(tokenResult)

    return({
        'status': 'success', 
        'vested': resJson
    })

  except Exception as e:
    logging.error(f'ERR:{myself()}: unable to build vesting request ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to build vesting request')

@r.get('/unspent', name="vesting:unspent")
def getUnspentExchange(tokenId=CFG.ergopadTokenId, allowMempool=True):
    logging.debug(f'TOKEN::{tokenId}')
    ergopadTokenBoxes = {}
    try:
        res = requests.get(f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}))
        if res.ok:
            for box in res.json():
                try: 
                    for asset in box['box']['assets']:
                        try:
                            assert asset['tokenId'] == tokenId
                            assert asset['amount'] > 0

                            boxId = box['box']['boxId']
                            if boxId in ergopadTokenBoxes:
                                ergopadTokenBoxes[boxId].append(asset)
                            else: 
                                ergopadTokenBoxes[boxId] = [asset]
                    
                        except: pass # tokens

                except: pass # assets

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find tokens for exchange ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to find tokens for exchange')

    return ergopadTokenBoxes
