from decimal import Decimal
import requests, json, os
import fractions
from sqlalchemy import create_engine
from starlette.responses import JSONResponse
from api.v1.routes.staking import AddressList
from core.auth import get_current_active_superuser 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, Depends, status
from typing import List, Optional
from pydantic import BaseModel
from time import sleep, time
from datetime import date, datetime, timezone, timedelta
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.util import encodeLong, encodeString
import uuid
from api.v1.routes.blockchain import ergusdoracle, getNFTBox, getTokenBoxes, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens, getBoxesWithUnspentTokens_beta
from ergo.appkit import ErgoAppKit, ErgoValueT
from hashlib import blake2b
from cache.cache import cache

from org.ergoplatform.appkit import Address, InputBox
from sigmastate.Values import ErgoTree

vesting_router = r = APIRouter()

CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

nergsPerErg        = 1000000000
headers            = {'Content-Type': 'application/json'}

ergUsdOracleNFT = "011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"
sigusd = "81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a"

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
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'presale info not found.')

        # allowance is fully spent
        if res['spent_sigusd'] >= res['allowance_sigusd']:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'purchase limit reached.')

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

    vestmentWalletAddress = CFG.vestmentWalletAddress
    try:
        logging.info(vestmentWalletAddress)
        buyerWallet        = Wallet(vestment.wallet)
        nodeWallet         = Wallet(vestmentWalletAddress)
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
            'address': CFG.vestmentWalletAddress, 
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
        logging.debug(f'VestingWalletErgoTree::{Wallet(scVesting).ergoTree()}')
        params = {
            'nodeWallet': vestmentWalletAddress,
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
        ergopadTokenBoxes = getBoxesWithUnspentTokens_beta(tokenId=CFG.validCurrencies[vs.vestedToken], nErgAmount=txFee_nerg*3, tokenAmount=tokenAmount)
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

def redeemTX(inBoxes, outBoxes, txBoxTotal_nerg, txFee_nerg):
    # redeem
    result = ""
    if len(outBoxes) > 0:
        inBoxesRaw = []
        txFee = max(txFee_nerg,(len(outBoxes)+len(inBoxes))*200000)
        ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId="", nErgAmount=txBoxTotal_nerg+txFee+txFee_nerg, tokenAmount=0,emptyRegisters=True)
        for box in inBoxes+list(ergopadTokenBoxes.keys()):
            res = requests.get(f'{CFG.node}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
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
        res = requests.post(f'{CFG.node}/wallet/transaction/send', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), json=request)   
        logging.debug(res)
        result = res.content
        return result

# redeem/disburse tokens after lock
@r.get("/redeem/{address}", name="vesting:redeem")
def redeemToken(address:str, numBoxes:Optional[int]=200):

    txFee_nerg = CFG.txFee
    txBoxTotal_nerg = 0
    #scPurchase = getErgoscript('alwaysTrue', {})
    outBoxes = []
    inBoxes = []
    currentTime = requests.get(f'{CFG.node}/blocks/lastHeaders/1', headers=dict(headers),timeout=2).json()[0]['timestamp']
    offset = 0
    res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers), timeout=2) #This needs to be put in a loop in case of more than 500 boxes
    while res.ok:
        rJson = res.json()
        logging.info(rJson['total'])
        for box in rJson['items']:
            if len(inBoxes) >= numBoxes:
                redeemTX(inBoxes,outBoxes,txBoxTotal_nerg,txFee_nerg)
                inBoxes = []
                outBoxes = []
                txBoxTotal_nerg = 0
                sleep(10)
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
                nodeRes = requests.get(f"{CFG.node}/utils/ergoTreeToAddress/{box['additionalRegisters']['R4']['renderedValue']}").json()
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
        result = redeemTX(inBoxes,outBoxes,txBoxTotal_nerg,txFee_nerg)
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

class RedeemWithNFTRequest(BaseModel):
    boxId: str
    address: str
    utxos: List[str] = []

@r.post("/redeemWithNFT", name="vesting:redeemWithNFT")
async def redeemWithNFT(req: RedeemWithNFTRequest):
    appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
    vestingBox = appKit.getBoxesById([req.boxId])[0]
    vestingBoxJson = json.loads(vestingBox.toJson(False))
    vestingKey = vestingBoxJson["additionalRegisters"]["R5"][4:]
    parameters = appKit.deserializeLongArray(vestingBoxJson["additionalRegisters"]["R4"])
    blockTime           = int(time()*1000)
    redeemPeriod        = parameters[0]
    numberOfPeriods     = parameters[1]
    vestingStart        = parameters[2]
    totalVested         = parameters[3]

    timeVested          = blockTime - vestingStart
    periods             = int(timeVested/redeemPeriod)
    redeemed            = totalVested - int(vestingBoxJson["assets"][0]["amount"])
    totalRedeemable     = int(periods * totalVested / numberOfPeriods)

    redeemableTokens    = totalVested - redeemed if (periods >= numberOfPeriods) else totalRedeemable - redeemed

    if len(req.utxos) == 0:
        tokensToSpend = {vestingKey: 1}
        userInputs = appKit.boxesToSpend(req.address,int(2e6),tokensToSpend)
    else:
        userInputs = appKit.getBoxesById(req.utxos)

    keyBox = None
    otherBoxes = []

    for box in userInputs:
        keyFound = False
        for token in box.getTokens():
            if token.getId().toString() == vestingKey:
                keyBox = box
                keyFound=True
        if not keyFound:
            otherBoxes.append(box)

    userInputs = [keyBox] #+ list(otherBoxes)

    outputs = []
    tokens={
            vestingBoxJson["assets"][0]["tokenId"]: redeemableTokens
        }
    if periods < numberOfPeriods:
        outputs.append(appKit.buildOutBox(
            value=vestingBox.getValue(),
            tokens={
                vestingBoxJson["assets"][0]["tokenId"]: (totalVested-(redeemed+redeemableTokens))
            },
            registers=list(vestingBox.getRegisters()),
            contract=appKit.contractFromTree(vestingBox.getErgoTree())
        ))
        tokens[vestingKey] = 1 
    outputs.append(appKit.buildOutBox(
        value=int(1e6),
        tokens=tokens,
        registers=None,
        contract=appKit.contractFromTree(userInputs[0].getErgoTree())
    ))

    unsignedTx = appKit.buildUnsignedTransaction(
        inputs=[vestingBox] + list(userInputs),
        outputs=outputs,
        fee=int(1e6),
        sendChangeTo=Address.create(req.address).getErgoAddress()
    )

    return appKit.unsignedTxToJson(unsignedTx)

@r.post("/vestedWithNFT/", name="vesting:vestedWithNFT")
async def vested(req: AddressList):
    CACHE_TTL = 600 # 10 mins
    vestingAddress = '2k6J5ocjeESe4cuXP6rwwq55t6cUwiyqDzNdEFgnKhwnWhttnSShZb4LaMmqTndrog6MbdT8iJbnnwWEcNoeRfEqXBQW4ohBTgm8rDnu9WBBZSixjJoKPT4DStGSobBkoxS4HZMe4brCgujdnmnMBNf8s4cfGtJsxRqGwtLMvmP6Z6FAXw5pYveHRFDBZkhh6qbqoetEKX7ER2kJormhK266bPDQPmFCcsoYRdRiUJBtLoQ3fq4C6N2Mtb3Jab4yqjvjLB7JRTP82wzsXNNbjUsvgCc4wibpMc8MqJutkh7t6trkLmcaH12mAZBWiVhwHkCYCjPFcZZDbr7xeh29UDcwPQdApxHyrWTWHtNRvm9dpwMRjnG2niddbZU82Rpy33cMcN3cEYZajWgDnDKtrtpExC2MWSMCx5ky3t8C1CRtjQYX2yp3x6ZCRxG7vyV7UmfDHWgh9bvU'
    try:
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
        vestingKeys = {}
        for address in req.addresses:
            # cache balance confirmed
            ok = False
            data = None
            cached = cache.get(f"get_vesting_vested_addresses_{address}_balance_confirmed")
            if cached:
                ok = True
                data = cached
            else:
                res = requests.get(f'{CFG.explorer}/addresses/{address}/balance/confirmed')
                ok = res.ok
                if ok:
                    data = res.json()
                    cache.set(f"get_vesting_vested_addresses_{address}_balance_confirmed", data, CACHE_TTL)
            if ok:
                if 'tokens' in data:
                    for token in data["tokens"]:
                        if 'name' in token and 'tokenId' in token:
                            if token["name"] is not None:
                                if "Vesting Key" in token["name"]:
                                    vestingKeys[token["tokenId"]] = address
            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failure to fetch balance for {address}')
        
        vested = {}
        
        # getTokenBoxes from cache
        checkBoxes = []
        cached = cache.get(f"get_vesting_vested_token_boxes")
        if cached:
            checkBoxes = cached
        else:
            appKitBoxes = appKit.getUnspentBoxes(vestingAddress)
            for appKitBox in appKitBoxes:
                checkBoxes.append(json.loads(appKitBox.toJson(False)))
            cache.set(f"get_vesting_vested_token_boxes", checkBoxes, CACHE_TTL)
        for box in checkBoxes:
            if box["additionalRegisters"]["R5"][4:] in vestingKeys.keys():
                parameters = appKit.deserializeLongArray(box["additionalRegisters"]["R4"])
                blockTime           = int(time()*1000)

                redeemPeriod        = parameters[0]
                numberOfPeriods     = parameters[1]
                vestingStart        = parameters[2]
                totalVested         = parameters[3]

                timeVested          = blockTime - vestingStart
                periods             = int(timeVested/redeemPeriod)
                redeemed            = totalVested - int(box["assets"][0]["amount"])
                totalRedeemable     = int(periods * totalVested / numberOfPeriods)

                redeemableTokens    = totalVested - redeemed if (periods >= numberOfPeriods) else totalRedeemable - redeemed
                vestedTokenInfo = getTokenInfo(box["assets"][0]["tokenId"])
                if vestedTokenInfo["name"] not in vested:
                    vested[vestedTokenInfo["name"]] = []
                vested[vestedTokenInfo["name"]].append({
                    'boxId': box["boxId"],
                    'Remaining': round(box["assets"][0]["amount"]*10**(-1*vestedTokenInfo["decimals"]),vestedTokenInfo["decimals"]),
                    'Redeemable': round(redeemableTokens*10**(-1*vestedTokenInfo["decimals"]),vestedTokenInfo["decimals"]),
                    'Vesting Key Id': box["additionalRegisters"]["R5"][4:],
                    'Next unlock': datetime.fromtimestamp((vestingStart+((periods+1)*redeemPeriod))/1000)
                })

        return vested
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Undefined error during staked')

class BootstrapRoundRequest(BaseModel):
    roundName: str
    tokenId: str
    roundAllocation: Decimal
    vestingPeriods: int
    vestingPeriodDuration_ms: int
    vestingStart_ms: int
    tokenSigUSDPrice: Decimal
    whitelistTokenMultiplier: Decimal
    sellerAddress: str

@r.post('/bootstrapRound', name="vesting:bootstrapRound")
async def bootstrapRound(
    req: BootstrapRoundRequest, 
    current_user=Depends(get_current_active_superuser)
):
    vestedToken = getTokenInfo(req.tokenId)
    vestedTokenAmount = int(req.roundAllocation*10**vestedToken["decimals"])

    appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")

    ergoPadContract = appKit.contractFromAddress(CFG.ergopadWallet)
    sellerContract = appKit.contractFromAddress(req.sellerAddress)

    initialInputs = appKit.boxesToSpend(CFG.ergopadWallet, int(5e6), {req.tokenId: vestedTokenAmount})

    nftId = initialInputs[0].getId().toString()

    presaleRoundNFTBox = appKit.mintToken(
                            value=int(1e6),
                            tokenId=nftId,
                            tokenName=f"{req.roundName}",
                            tokenDesc="NFT identifying the presale round box",
                            mintAmount=1,
                            decimals=0,
                            contract=ergoPadContract)
    tokenBox = appKit.buildOutBox(
        value = int(3e6),
        tokens = {req.tokenId: vestedTokenAmount},
        registers = None,
        contract=ergoPadContract
    )

    nftMintUnsignedTx = appKit.buildUnsignedTransaction(
                            inputs=initialInputs,
                            outputs=[presaleRoundNFTBox,tokenBox],
                            fee=int(1e6),
                            sendChangeTo=ergoPadContract.toAddress().getErgoAddress())

    nftMintSignedTx = appKit.signTransactionWithNode(nftMintUnsignedTx)

    appKit.sendTransaction(nftMintSignedTx)

    whitelistTokenId = nftMintSignedTx.getOutputsToSpend()[0].getId().toString()

    whiteListTokenBox = appKit.mintToken(
                            value=int(1e6),
                            tokenId=whitelistTokenId,
                            tokenName=f"{req.roundName} whitelist token",
                            tokenDesc=f"Token proving allocation for the {req.roundName} round",
                            mintAmount=int(vestedTokenAmount*req.whitelistTokenMultiplier),
                            decimals=vestedToken["decimals"],
                            contract=ergoPadContract)

    sigusd = "81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a"
    ergusdoracle = "011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"

    with open(f'contracts/NFTLockedVesting.es') as f:
        script = f.read()
    nftLockedVestingContractTree = appKit.compileErgoScript(script)

    with open(f'contracts/proxyNFTLockedVesting.es') as f:
        script = f.read()
    proxyNftLockedVestingTree = appKit.compileErgoScript(
        script,
        {
            "_NFTLockedVestingContract": appKit.ergoValue(blake2b(bytes.fromhex(nftLockedVestingContractTree.bytesHex()), digest_size=32).digest(), ErgoValueT.ByteArray).getValue(),
            "_ErgUSDOracleNFT": appKit.ergoValue(ergusdoracle, ErgoValueT.ByteArrayFromHex).getValue(),
            "_SigUSDTokenId": appKit.ergoValue(sigusd, ErgoValueT.ByteArrayFromHex).getValue()     
        }
    )

    price = fractions.Fraction(req.tokenSigUSDPrice*10**Decimal(int(2-vestedToken["decimals"])))
    proxyContractBox = appKit.buildOutBox(
        value = int(1e6),
        tokens = {
            nftId: 1,
            req.tokenId: vestedTokenAmount
        },
        registers=[
            appKit.ergoValue(
                [
                    req.vestingPeriodDuration_ms,   #redeemPeriod
                    req.vestingPeriods,             #numberOfPeriods
                    req.vestingStart_ms,            #vestingStart
                    price.numerator,                #priceNum
                    price.denominator               #priceDenom
                ], ErgoValueT.LongArray),
            appKit.ergoValue(req.tokenId, ErgoValueT.ByteArrayFromHex),                  #vestedTokenId
            appKit.ergoValue(sellerContract.getErgoTree().bytes(), ErgoValueT.ByteArray), #Seller address
            appKit.ergoValue(whitelistTokenId, ErgoValueT.ByteArrayFromHex)              #Whitelist tokenid
        ],
        contract=appKit.contractFromTree(proxyNftLockedVestingTree)
    )

    bootstrapUnsigned = appKit.buildUnsignedTransaction(
        inputs=[nftMintSignedTx.getOutputsToSpend()[0],nftMintSignedTx.getOutputsToSpend()[1]],
        outputs=[whiteListTokenBox,proxyContractBox],
        fee=int(1e6),
        sendChangeTo=ergoPadContract.toAddress().getErgoAddress()
    )

    bootstrapSigned = appKit.signTransactionWithNode(bootstrapUnsigned)

    appKit.sendTransaction(bootstrapSigned)

    return {
        'Whitelist token id': whitelistTokenId,
        'Proxy NFT': nftId,
        'NFT mint transaction': nftMintSignedTx.getId(),
        'Whitelist token mint and token lock transaction': bootstrapSigned.getId(),
        'Proxy address': appKit.contractFromTree(proxyNftLockedVestingTree).toAddress().toString()
    }

@r.get('/activeRounds', name='vesting:activeRounds')
async def activeRounds():
    proxyAddress = 'Jf7SDZuaVDGiCwCxC7N2y8cuptH3cgNT1nteJK469effW2gNarYn1AxsYjNcP7zYtvzmVjNPMmE3PYJRMC2E7m3yTDBrHvv9BQ1uoBZ9ijAHnZduK58qcephAxQdgRLkjg31phyvByEu2sbwigdsKbp4vRzXbQjL7Mip4pR9BwCAfGRir27nFnXpcAV4HGBgfTDgsd7ZdEJiHETwxHkMkGNge5KCd6opPUKTHcnVkxN8bUb21DhwHqYDUwKfPsYZ2cmpEgUjp2Nk9J82GfC9ien2Qv99kFnJbAvr7cXQx47PTbH7mp5coDZQa4jweBBUMTTwdyDmHaNxHXo7HiLetMViswACR6PQ5VouP57QSRjEPzFDGVjACBSrKSKwH9Sb8Zo93Q8KrRpVpKfKKtJQ9wrEy5SSfg3kFyM23dhkhaMkDbManVHboxpHXPGkDY7djNjpk91bWPhYhyqDDC6tGGEnVn3zxNjzcJaxutzkjQXabpUTb1toQN2jRgN37Kh4agvpdPjJ8pQhUvBMPUBA1HYLH3JirDmir88oXby2kUi2V7bF4XVjr6JLcz6hjVut19MKncrp715Vf3dhiAMv3K5S88YvzKVJrC6nnVniqgWmthQGF7FyzMSAdaqK9m7BWNquLSW3etPaM42DSxdT4HboAwxN9qk3sevQyuvT3GAC5BiAzNAt9jE3kxoMu6mJVCg59mX6oVcriqUTYtXpjFASTjUJD9Lp1cZMK3JgWj7Pi6BbtqNs2qny2hXZqNHhm7TWVoVMwFB39nD1tXBJEQhu6Gfw6LcnDfxTKWj2AVLTdvkqqW8RSaFrCAxuQhqvEdE5NeHg1PqP2gdS4JhMGwBgkDwnDqJQyPN4NmKP1ncXcVXKVF1VxJ28ZxQe8kQ3VJQqEnhqah'
    appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
    proxyBoxes = appKit.getUnspentBoxes(proxyAddress)
    result = {'activeRounds': [], 'soldOutRounds': []}
    for proxyBox in proxyBoxes:
        logging.info(proxyBox)
        tokens = list(proxyBox.getTokens())
        roundInfo = getTokenInfo(tokens[0].getId().toString())
        if len(tokens) > 1:
            vestedInfo = getTokenInfo(tokens[1].getId().toString())
            whitelistTokenId = list(proxyBox.getRegisters())[3].toHex()[4:]
            result['activeRounds'].append({
                'roundName': roundInfo["name"], 
                'proxyNFT': tokens[0].getId().toString(), 
                'remaining': tokens[1].getValue()*10**(-1*vestedInfo["decimals"]),
                'Whitelist tokenId': whitelistTokenId
                })
        else:
            result['soldOutRounds'].append({'roundName': roundInfo["name"], 'proxyNFT': tokens[0].getId().toString()})
    return result

class RequiredNergTokensRequest(BaseModel):
    proxyNFT: str
    vestingAmount: Decimal
    sigUSDAmount: Decimal

@r.post('/requiredNergTokens', name="vesting:requiredNergTokens")
async def requiredNergTokens(req: RequiredNergTokensRequest):
    proxyBox = getNFTBox(req.proxyNFT)
    whitelistTokenId = proxyBox["additionalRegisters"]["R7"]["renderedValue"]
    vestedTokenId = proxyBox["additionalRegisters"]["R5"]["renderedValue"]
    roundParameters = eval(proxyBox["additionalRegisters"]["R4"]["renderedValue"])
    priceNum = roundParameters[3]
    priceDenom = roundParameters[4]
    vestedTokenInfo = getTokenInfo(vestedTokenId)
    oracleInfo = await ergusdoracle()
    nErgPerUSD = oracleInfo["latest_datapoint"]
    sigUsdDecimals = int(2)
    sigUsdTokens = int(req.sigUSDAmount*10**sigUsdDecimals)
    whitelistTokens = int(req.vestingAmount*10**vestedTokenInfo["decimals"])
    requiredSigUSDTokens = int(whitelistTokens*priceNum/priceDenom)
    nergRequired = int((requiredSigUSDTokens-sigUsdTokens)*(nErgPerUSD*10**(-1*sigUsdDecimals)))

    result = {
        'nErgRequired': nergRequired,
        'tokens': [
            {
                'tokenId': whitelistTokenId,
                'amount': whitelistTokens
            }
        ]
    }

    if sigUsdTokens > 0:
        result['tokens'].append({'tokenId': sigusd, 'amount': sigUsdTokens})

    return result

class VestFromProxyRequest(RequiredNergTokensRequest):   
    address: str
    utxos: List[str] = []

@r.post('/vestFromProxy', name="vesting:vestFromProxy")
async def vestFromProxy(req: VestFromProxyRequest):
    try:
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
        proxyBox = getNFTBox(req.proxyNFT)
        if proxyBox is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failed to retrieve proxy box')
        roundInfo = getTokenInfo(req.proxyNFT)
        whitelistTokenId = proxyBox["additionalRegisters"]["R7"]["renderedValue"]
        vestedTokenId = proxyBox["additionalRegisters"]["R5"]["renderedValue"]
        sellerAddress = proxyBox["additionalRegisters"]["R6"]["renderedValue"]
        roundParameters = eval(proxyBox["additionalRegisters"]["R4"]["renderedValue"])
        priceNum = roundParameters[3]
        priceDenom = roundParameters[4]
        vestedTokenInfo = getTokenInfo(vestedTokenId)
        oracleInfo = getNFTBox(ergUsdOracleNFT)
        if oracleInfo is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failed to retrieve oracle box')
        nErgPerUSD = int(oracleInfo["additionalRegisters"]["R4"]["renderedValue"])
        sigUsdDecimals = int(2)
        sigUsdTokens = int(req.sigUSDAmount*10**sigUsdDecimals)
        whitelistTokens = int(req.vestingAmount*10**vestedTokenInfo["decimals"])
        requiredSigUSDTokens = int(whitelistTokens*priceNum/priceDenom)
        nergRequired = int((requiredSigUSDTokens-sigUsdTokens)*(nErgPerUSD*10**(-1*sigUsdDecimals)))
        userInputs = List[InputBox]
        if len(req.utxos) == 0:
            tokensToSpend = {whitelistTokenId: whitelistTokens}
            if req.sigUSDAmount>0:
                tokensToSpend[sigusd] = sigUsdTokens
            userInputs = appKit.boxesToSpend(req.address,int(4e6+nergRequired),tokensToSpend)
        else:
            userInputs = appKit.getBoxesById(req.utxos)
        if userInputs is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not find input boxes')
        inputs = list(appKit.getBoxesById([proxyBox["boxId"]])) + list(userInputs)
        dataInputs = list(appKit.getBoxesById([oracleInfo["boxId"]]))
        proxyOutput = appKit.buildOutBox(
            value = inputs[0].getValue(),
            tokens = {
                req.proxyNFT: 1,
                vestedTokenId: inputs[0].getTokens()[1].getValue()-whitelistTokens
            },
            registers=list(inputs[0].getRegisters()),
            contract=appKit.contractFromTree(inputs[0].getErgoTree())
        )
        with open(f'contracts/NFTLockedVesting.es') as f:
            script = f.read()
        nftLockedVestingContractTree = appKit.compileErgoScript(script)
        vestingOutput = appKit.buildOutBox(
            value=int(1e6),
            tokens={
                vestedTokenId: whitelistTokens
            },
            registers=[
                appKit.ergoValue([
                    roundParameters[0],
                    roundParameters[1],
                    roundParameters[2],
                    whitelistTokens
                ],ErgoValueT.LongArray),
                appKit.ergoValue(proxyBox["boxId"],ErgoValueT.ByteArrayFromHex)
            ],
            contract=appKit.contractFromTree(nftLockedVestingContractTree)
        )
        userOutput = appKit.mintToken(
            value=int(1e6),
            tokenId=proxyBox["boxId"],
            tokenName=f"{roundInfo['name']} Vesting Key",
            tokenDesc=f'{{"Vesting Round": {roundInfo["name"]}, "Vesting start": "{datetime.fromtimestamp(roundParameters[2]/1000)}", "Periods": {roundParameters[1]}, "Period length": "{timedelta(milliseconds=roundParameters[0]).days} day(s)", "Total vested": {req.vestingAmount} }}',
            mintAmount=1,
            decimals=0,
            contract=appKit.contractFromTree(userInputs[0].getErgoTree())
        )
        sellerOutput = appKit.buildOutBox(
            value=int(1e6)+nergRequired,
            tokens=tokensToSpend,
            registers=None,
            contract=appKit.contractFromTree(appKit.treeFromBytes(bytes.fromhex(sellerAddress)))
        )

        unsignedTx = appKit.buildUnsignedTransaction(
            inputs=inputs,
            outputs=[proxyOutput,vestingOutput,userOutput,sellerOutput],
            dataInputs=dataInputs,
            fee=int(1e6),
            sendChangeTo=Address.create(req.address).getErgoAddress()
        )

        # signedTx = appKit.signTransactionWithNode(unsignedTx)

        # return appKit.sendTransaction(signedTx)

        return appKit.unsignedTxToJson(unsignedTx)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Uncaught error: {e}')


