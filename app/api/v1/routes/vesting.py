from decimal import Decimal
import requests, json, os
import fractions
import re
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
from api.v1.routes.blockchain import TXFormat, ergusdoracle, getNFTBox, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens, getBoxesWithUnspentTokens_beta, getUnspentBoxesByTokenId
from hashlib import blake2b
from cache.cache import cache

from ergo_python_appkit.appkit import ErgoAppKit, ErgoValueT
from org.ergoplatform.appkit import Address, ErgoClientException, InputBox
from sigmastate.Values import ErgoTree

vesting_router = r = APIRouter()

CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

nergsPerErg        = 1000000000
headers            = {'Content-Type': 'application/json'}

ergUsdOracleNFT = "011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"
sigusd = "03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04"

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
    try:
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

    except Exception as e:
        logging.error(f'ERR:{myself()}: get scenario ({e})')
        return

# purchase tokens
@r.post("/vest/", name="vesting:vestToken")
async def vestToken(vestment: Vestment): 
    try:
        # deprecated May 2022; shutting down beta
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Invalid endpoint, please contact support.')

        st = int(time())
        vs = getScenario(vestment.vestingScenario)
        if vs is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unknown vesting scenario ({vestment.vestingScenario})')
        if not vs.enabled:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Disabled vesting scenario, ({vestment.vestingScenario})')

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

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to vest.')

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
        logging.error(f'ERR:{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Invalid token decimals.')

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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to build request.')

def redeemTX(inBoxes, outBoxes, txBoxTotal_nerg, txFee_nerg):
    try:
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

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to redeem transaction ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to redeem transaction')

# redeem/disburse tokens after lock
@r.get("/redeem/{address}", name="vesting:redeem")
def redeemToken(address:str, numBoxes:Optional[int]=200):
    try:
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

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to redeem.')

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
        logging.error(f'ERR:{myself()}: unable to redeem token ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to redeem token.')

# find vesting/vested tokens
@r.get("/vested/{wallet}", name="vesting:findVestedTokens")
def findVestingTokens(wallet:str):
    try:
        #tokenId = CFG.ergopadTokenId
        total = 0
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to build vesting request.')

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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to find tokens for exchange.')

    return ergopadTokenBoxes

class RedeemWithNFTRequest(BaseModel):
    boxId: str
    address: str
    utxos: List[str] = []
    txFormat: TXFormat = TXFormat.EIP_12
    addresses: List[str] = []

@r.post("/redeemWithNFT", name="vesting:redeemWithNFT")
async def redeemWithNFT(req: RedeemWithNFTRequest):
    try:
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
        vestingBox = appKit.getBoxesById([req.boxId])[0]
        vestingBoxJson = json.loads(vestingBox.toJson(False))
        vestingKey = vestingBoxJson["additionalRegisters"]["R5"][4:]
        parameters = ErgoAppKit.deserializeLongArray(vestingBoxJson["additionalRegisters"]["R4"])
        blockTime           = int(time()*1000)
        redeemPeriod        = parameters[0]
        numberOfPeriods     = parameters[1]
        vestingStart        = parameters[2]
        totalVested         = parameters[3]

        timeVested          = blockTime - vestingStart
        periods             = max(0,int(timeVested/redeemPeriod))
        redeemed            = totalVested - int(vestingBoxJson["assets"][0]["amount"])
        if vestingBoxJson["ergoTree"] == "1012040204000404040004020406040c0408040a050004000402040204000400040404000400d812d601b2a4730000d602e4c6a7050ed603b2db6308a7730100d6048c720302d605db6903db6503fed606e4c6a70411d6079d997205b27206730200b27206730300d608b27206730400d609b27206730500d60a9972097204d60b95917205b272067306009d9c7209b27206730700b272067308007309d60c959272077208997209720a999a9d9c7207997209720b7208720b720ad60d937204720cd60e95720db2a5730a00b2a5730b00d60fdb6308720ed610b2720f730c00d6118c720301d612b2a5730d00d1eded96830201aedb63087201d901134d0e938c721301720293c5b2a4730e00c5a79683050193c2720ec2720193b1720f730f938cb2720f731000017202938c7210017211938c721002720cec720dd801d613b2db630872127311009683060193c17212c1a793c27212c2a7938c7213017211938c721302997204720c93e4c67212050e720293e4c6721204117206":
            tgeNum              = parameters[4]
            tgeDenom            = parameters[5]
            tgeTime             = parameters[6]
            tgeAmount           = int(totalVested * tgeNum / tgeDenom) if (blockTime > tgeTime) else 0
            totalRedeemable     = int(periods * (totalVested-tgeAmount) / numberOfPeriods) + tgeAmount
        else:
            totalRedeemable     = int(periods * totalVested / numberOfPeriods)

        redeemableTokens    = totalVested - redeemed if (periods >= numberOfPeriods) else totalRedeemable - redeemed
        tokensToSpend = {vestingKey: 1}
        if len(req.utxos) == 0:
            userInputs = appKit.boxesToSpend(req.address,int(2e6),tokensToSpend)
        else:
            userInputs = appKit.getBoxesById(req.utxos)

        if len(req.utxos) == 0:
            if len(req.addresses) == 0:
                userInputs = appKit.boxesToSpend(req.address,int(2e6),tokensToSpend)
            else:
                userInputs = appKit.boxesToSpendFromList(req.addresses,int(2e6),tokensToSpend)
        else:
            userInputs = appKit.getBoxesById(req.utxos)
            if not ErgoAppKit.boxesCovered(userInputs,int(2e6),tokensToSpend):
                userInputs = appKit.boxesToSpend(req.address,int(2e6),tokensToSpend)

        if userInputs is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not find enough erg and/or tokens')

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

        userInputs = [keyBox] + list(otherBoxes)

        userInputs = ErgoAppKit.cutOffExcessUTXOs(userInputs,int(2e6),tokensToSpend)

        outputs = []
        tokens={
                vestingKey: 1, 
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

        if req.txFormat == TXFormat.EIP_12:
            return ErgoAppKit.unsignedTxToJson(unsignedTx)

        if req.txFormat == TXFormat.ERGO_PAY:
            reducedTx = appKit.reducedTx(unsignedTx)
            ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                reducedTx,
                address=req.address
            )
            cache.set(f'ergopay_signing_request_{unsignedTx.getId()}',ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{unsignedTx.getId()}'}

    except Exception as e:
        content = f'Unable to redeem with NFT.'
        # found match with "reason"
        m = re.search('reason: NotEnoughErgsError\(not enough boxes to meet ERG needs (\d+) \(found only (\d+)\),\d+\)\)', str(e))
        if m is not None:
             content = f'transaction requires {(m.group(0)/10e9):,.3} ergs, and only {(m.group(1)/10e9):,.3} ergs were found.'
        logging.error(f'ERR:{myself()}: {content} ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)


@r.post("/vestedWithNFT/", name="vesting:vestedWithNFT")
async def vested(req: AddressList):
    CACHE_TTL = 600 # 10 mins
    vestingAddresses = [
        '2k6J5ocjeESe4cuXP6rwwq55t6cUwiyqDzNdEFgnKhwnWhttnSShZb4LaMmqTndrog6MbdT8iJbnnwWEcNoeRfEqXBQW4ohBTgm8rDnu9WBBZSixjJoKPT4DStGSobBkoxS4HZMe4brCgujdnmnMBNf8s4cfGtJsxRqGwtLMvmP6Z6FAXw5pYveHRFDBZkhh6qbqoetEKX7ER2kJormhK266bPDQPmFCcsoYRdRiUJBtLoQ3fq4C6N2Mtb3Jab4yqjvjLB7JRTP82wzsXNNbjUsvgCc4wibpMc8MqJutkh7t6trkLmcaH12mAZBWiVhwHkCYCjPFcZZDbr7xeh29UDcwPQdApxHyrWTWHtNRvm9dpwMRjnG2niddbZU82Rpy33cMcN3cEYZajWgDnDKtrtpExC2MWSMCx5ky3t8C1CRtjQYX2yp3x6ZCRxG7vyV7UmfDHWgh9bvU',
        'HNLdwoHRsUSevguzRajzvy1DLAvUJ9YgQezQq6GGZiY4TmU9VDs2ae8mRpQkfEnLmuUKyJibZD2bXR2yoo1p8T5WCRKPn4rJVJ2VR2LvRBk8ViCmhcume5ubWaySXTUqpftEaaURTM6KSFxe4QbRFbToyPzZ3JJmjoDn4WzHh5ioXZMj7AX6xTwJvFmzPuko9BqDk5z1RJtD1wP4kd8sSsLN9P2YNQxmUGDEBYHaDCoAhY7Pg5oKit6ZyqMynoiycWqctfg1EHhMUKCTJsZNnidU961ri98RaYP4CfEwYQ3d9dRVuC6S1n7J1wPPHYqmUBgJCGWbTULayXUowSSmRuZUkQYGo9vvNaEpB7ManiLsX1n8cBYwN4XoVsY24mCfptBP86P4rZ5fgcr9mYtQ9nG934DMDZBbjs81VzCupB6KVrGCe1WtYSr6c1DwkNAinBMwqcqxTznXZUvfBsjDSCtJzCut44xcc7Zsy9mWz2B2pqhdKsX83BVzMDDM5hnjXTShYfauJGs81']
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
            for vestingAddress in vestingAddresses:
                appKitBoxes = appKit.getUnspentBoxes(vestingAddress)
                for appKitBox in appKitBoxes:
                    checkBoxes.append(json.loads(appKitBox.toJson(False)))
            cache.set(f"get_vesting_vested_token_boxes", checkBoxes, CACHE_TTL)
        for box in checkBoxes:
            if box["additionalRegisters"]["R5"][4:] in vestingKeys.keys():
                parameters = ErgoAppKit.deserializeLongArray(box["additionalRegisters"]["R4"])
                blockTime           = int(time()*1000)

                redeemPeriod        = parameters[0]
                numberOfPeriods     = parameters[1]
                vestingStart        = parameters[2]
                totalVested         = parameters[3]

                timeVested          = blockTime - vestingStart
                periods             = max(0,int(timeVested/redeemPeriod))
                redeemed            = totalVested - int(box["assets"][0]["amount"])
                if box["ergoTree"] == "1012040204000404040004020406040c0408040a050004000402040204000400040404000400d812d601b2a4730000d602e4c6a7050ed603b2db6308a7730100d6048c720302d605db6903db6503fed606e4c6a70411d6079d997205b27206730200b27206730300d608b27206730400d609b27206730500d60a9972097204d60b95917205b272067306009d9c7209b27206730700b272067308007309d60c959272077208997209720a999a9d9c7207997209720b7208720b720ad60d937204720cd60e95720db2a5730a00b2a5730b00d60fdb6308720ed610b2720f730c00d6118c720301d612b2a5730d00d1eded96830201aedb63087201d901134d0e938c721301720293c5b2a4730e00c5a79683050193c2720ec2720193b1720f730f938cb2720f731000017202938c7210017211938c721002720cec720dd801d613b2db630872127311009683060193c17212c1a793c27212c2a7938c7213017211938c721302997204720c93e4c67212050e720293e4c6721204117206":
                    tgeNum              = parameters[4]
                    tgeDenom            = parameters[5]
                    tgeTime             = parameters[6]
                    tgeAmount           = int(totalVested * tgeNum / tgeDenom) if (blockTime > tgeTime) else 0
                    totalRedeemable     = int(periods * (totalVested-tgeAmount) / numberOfPeriods) + tgeAmount
                else:
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to vest with NFT.')

class BootstrapRoundRequest(BaseModel):
    roundName: str
    tokenId: str
    roundAllocation: Decimal
    vestingPeriods: int
    vestingPeriodDuration_ms: int
    cliff_ms: int
    tokenSigUSDPrice: Decimal
    whitelistTokenMultiplier: Decimal
    sellerAddress: str
    tgeTime_ms: int
    tgePct: int
    roundEnd_ms: int

@r.post('/bootstrapRound', name="vesting:bootstrapRound")
async def bootstrapRound(
    req: BootstrapRoundRequest, 
    current_user=Depends(get_current_active_superuser)
):
    try:
        vestedToken = getTokenInfo(req.tokenId)
        vestedTokenAmount = int(req.roundAllocation*10**vestedToken["decimals"])

        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/",CFG.ergopadApiKey)

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

        sigusd = "03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04"
        ergusdoracle = "011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"

        with open(f'contracts/NFTLockedVestingV2.es') as f:
            script = f.read()
        nftLockedVestingContractTree = appKit.compileErgoScript(script)

        with open(f'contracts/proxyNFTLockedVestingV2.es') as f:
            script = f.read()
        proxyNftLockedVestingTree = appKit.compileErgoScript(
            script,
            {
                "_NFTLockedVestingContract": ErgoAppKit.ergoValue(blake2b(bytes.fromhex(nftLockedVestingContractTree.bytesHex()), digest_size=32).digest(), ErgoValueT.ByteArray).getValue(),
                "_ErgUSDOracleNFT": ErgoAppKit.ergoValue(ergusdoracle, ErgoValueT.ByteArrayFromHex).getValue(),
                "_SigUSDTokenId": ErgoAppKit.ergoValue(sigusd, ErgoValueT.ByteArrayFromHex).getValue()     
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
                ErgoAppKit.ergoValue(
                    [
                        req.vestingPeriodDuration_ms,   #redeemPeriod
                        req.vestingPeriods,             #numberOfPeriods
                        req.tgeTime_ms + req.cliff_ms - req.vestingPeriodDuration_ms,  #vestingStart
                        price.numerator,                #priceNum
                        price.denominator,              #priceDenom
                        req.roundEnd_ms,                #Timestamp where token extraction is possible
                        req.tgePct,                     #tge percentage numerator
                        int(100),                       #tge percentage denominator
                        req.tgeTime_ms                  #timestamp for tge/ido
                    ], ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(req.tokenId, ErgoValueT.ByteArrayFromHex),                  #vestedTokenId
                ErgoAppKit.ergoValue(sellerContract.getErgoTree().bytes(), ErgoValueT.ByteArray), #Seller address
                ErgoAppKit.ergoValue(whitelistTokenId, ErgoValueT.ByteArrayFromHex)              #Whitelist tokenid
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

    except Exception as e:
        logging.error(f'ERR:{myself()}: Unable to bootstrap round. ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to bootstrap round.')


@r.get('/activeRounds', name='vesting:activeRounds')
async def activeRounds():
    try:
        proxyAddresses = [
            'Jf7SDZuaVDGiCwCxC7N2y8cuptH3cgNT1nteJK469effW2gNarYn1AxsYjNcP7zYtvzmVjNPMmE3PYJRMC2E7m3yTDBrHvv8voJM35a9ktLb3bNeQ4qEJSyFse3pQeqcTxvPATNAv7RHc3fnAkBf3PsNBGFoRq2nwnciNwUaNcunyfWz2JDbwrBzMT7gMfs8U9YKAKGU1V754PUa1WRccaUfWxDAj5zVVkzkvVNNeQPH2g9GAu539Kc5792XLRwfv5MqaBkQ6KqHw8tgck2e55G4sY6n9ZQ4vboeuVC9JzsuiYraAuc6Lbj1NbPdDRaHXBUAQioDuzRBFxDFwLdmsZXykdvDfJZDytxPoCkzdfMmr8Zchga8vELSydrJ8smXbjWnrySGTZWqcQbJLB1YwPDiGVQvDvvQhRSezJcGMXUXea9zX6cCaeAsrqCULonZKVoeVgCNGte6VFk7PTKJ5W5LrRW1cgkJNRHYrpqPujPN8SoMgLjt1zvCKww5eSuu2RXqyZNVPRxMU3uQd3F2hRjGAmJA6M8Mz5QdZmoXj1LRWnrz1C1E6z6mL1Unry2GYWbxfTsVFRbZVZEv78yn9TUN7cuA163BSoxLVeKwUbGC2uiWeWSm1FzTPNCHHpVtBRfTACKoNbxag9SGgxpsepyxaF7snbXhKtBnqFvyg2ZEiiHXUDjY1Qy8kjf9JrdLmifU6WaZ7VdhNEdHGpf72ivo5sVPNEeUKoKfHAY6WWokivYjeSpKCSLjougKwaNoR79tUWdfN8CEudwUSebWXD92cbnMZxS7QBvGqcUSGRQuuD1uXgeWF8m76xgVH4sQfTuMMvYVWeH8e8bHHqtQMzw2FUajFo2F1mxxwVqvkUQJgmRQXYBndDGiquVCvTqNdZ25eo32gf',
            'SA7vqpDWt8BYmP6PJxRe3TgV89iu6dhKr1sk622mW8PfxZ5WrcBZ4En3LwTmKJMvb2Cfzg4HPeK6wJ61aYKnqcFwkNh1bqPkk74KhespAF4Ga7YM3TNi33H8CtDLZXC69F8EyrMcsSex5taUYad9rBZm2kXZc1aLFEh9795wBsvXzoxPpALq82bBeVBij89gkaQ6Ny4c7QfAguqRzE8BkefSh75aGmcq7ZYtcRCuy5BMzVnWJBT4mrAwbDJBYxYdaSQ8zAvA7PA65zQvEVquLqamZg1PmApFL3aqbhjoF5Ppr2NHJeBdtgb9vMc9XDZy4Aag3V6EqujRoZ29WUQRTDp32iBNhEBTdE8PdSfpw5pZMzmSCGtCQ5eh5dXC4ahG8QL2D4NvXP78Qyu2FG6xyxo823G93Q2BqpcSesQvnz3bYrthVDMdBiiLqgwfsiXoTNg4KYk3HBftEzbfPnhTXxgrm8CcRWodKhS9tiA75WotZZcTACcrRZny7ZYETfwwSYTVasg7DxnSpZN4VPDExPigm69j8D8tp3hrP9BBESLWJF6EspxfWd4Nbx14eou4dQ4TRsxJUG5noCoXCeWEB4iyzuG9RyNTGD4h3gsAnnt8bR7FV6uWopmqHZ85Nyra5Zqh1aR6VQsbStaFL3WhSMS5pFBC5mhmuF7hdu3ZmsXsNgVEinGwM9jnukKghMBRNSpQbwqi4TZjja6fy93tUS9ggUShvRV7wE7YTKxq1RnnVQZTb6CCRvmycZFUuWehqXu7XekDUkWYPGC4KaagVbJRsXmKnqt36Re6V8NgHiTr4SjGzrj6gtbah1CfAVjVVA3Ggb1LnnXs4MFZpfmLnAGSm6PCb4Y3M53KygQ4pY7opZ1yxBAhB4tnJLa4KQj9uLy1V8mrK6xm8envCM92zhtPdAaxMZZmccQvSmMitSrVgWu419pT2yFTE6QpApZqysXtry3jRsmnEwLh72FfpE3xrfz4TBjM41tZm7RAEL8CwKfzs3qNsXCqvdLiBSdr6XTo9kTW6azMsGHLigqzg34FrkUGQW3S4aSnrapt1r7HmU9pGHukuuMcvgV4KrhPwV3chVetMLFEk4SoPavKueY4kX7KcAwEFsJcLtcXZq1kKBFS7kogsPNCnmxPj']
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
        with open(f'contracts/NFTLockedVestingV2.es') as f:
            script = f.read()
        nftLockedVestingContractTree = appKit.compileErgoScript(script)
        logging.info(appKit.contractFromTree(nftLockedVestingContractTree).getErgoTree().bytesHex())
        result = {'activeRounds': [], 'soldOutRounds': []}
        for proxyAddress in proxyAddresses:
            proxyBoxes = appKit.getUnspentBoxes(proxyAddress)
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

    except Exception as e:
        logging.error(f'ERR:{myself()}: Unable to determine proper round. ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to determine proper round.')

class RequiredNergTokensRequest(BaseModel):
    proxyNFT: str
    vestingAmount: Decimal
    sigUSDAmount: Decimal

@r.post('/requiredNergTokens', name="vesting:requiredNergTokens")
async def requiredNergTokens(req: RequiredNergTokensRequest):
    try:
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

    except Exception as e:
        logging.error(f'ERR:{myself()}: Unable to calculate required tokens for transaction. ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to calculate required tokens for transaction.')

class VestFromProxyRequest(RequiredNergTokensRequest):   
    address: str
    addresses: List[str] = []
    utxos: List[str] = []
    txFormat: TXFormat = TXFormat.EIP_12

@r.post('/contribute', name="vesting:contribute")
async def contribute(req: VestFromProxyRequest):
    try:
        oracleInfo = await ergusdoracle()
        if oracleInfo is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failed to retrieve oracle info')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
        proxyBox = getNFTBox(req.proxyNFT)
        if proxyBox is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failed to retrieve proxy box')
        #roundInfo = getTokenInfo(req.proxyNFT)
        whitelistTokenId = proxyBox["additionalRegisters"]["R7"]["renderedValue"]
        vestedTokenId = proxyBox["additionalRegisters"]["R5"]["renderedValue"]
        roundParameters = eval(proxyBox["additionalRegisters"]["R4"]["renderedValue"])
        priceNum = roundParameters[3]
        priceDenom = roundParameters[4]
        vestedTokenInfo = getTokenInfo(vestedTokenId)
        nErgPerUSD = int(oracleInfo["latest_datapoint"]*1.01)
        sigUsdDecimals = int(2)
        sigUsdTokens = int(req.sigUSDAmount*10**sigUsdDecimals)
        whitelistTokens = int(req.vestingAmount*10**vestedTokenInfo["decimals"])
        requiredSigUSDTokens = int(whitelistTokens*priceNum/priceDenom)
        nergRequired = int((requiredSigUSDTokens-sigUsdTokens)*(nErgPerUSD*10**(-1*sigUsdDecimals)))
        userInputs = List[InputBox]
        tokensToSpend = {whitelistTokenId: whitelistTokens}
        if req.sigUSDAmount>0:
            tokensToSpend[sigusd] = sigUsdTokens
        if len(req.utxos) == 0:
            if len(req.addresses) == 0:
                userInputs = appKit.boxesToSpend(req.address,int(22e6+nergRequired),tokensToSpend)
            else:
                userInputs = appKit.boxesToSpendFromList(req.addresses,int(22e6+nergRequired),tokensToSpend)
        else:
            userInputs = appKit.getBoxesById(req.utxos)
            if not ErgoAppKit.boxesCovered(userInputs,int(22e6+nergRequired),tokensToSpend):
                userInputs = appKit.boxesToSpend(req.address,int(22e6+nergRequired),tokensToSpend)
        logging.info("0")
        if userInputs is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not find enough erg and/or tokens')

        with open(f'contracts/userProxyNFTLockedVesting.es') as f:
            script = f.read()
        userProxyNFTLockedVestingContractTree = appKit.compileErgoScript(script,
            {
                "_ErgUSDOracleNFT": ErgoAppKit.ergoValue(ergUsdOracleNFT, ErgoValueT.ByteArrayFromHex).getValue()    
            })
        logging.info("1")
        proxyOutput = appKit.buildOutBox(
            value=int(22e6)+nergRequired,
            tokens=tokensToSpend,
            registers=[
                ErgoAppKit.ergoValue(nErgPerUSD,ErgoValueT.Long),
                ErgoAppKit.ergoValue(Address.create(req.address).toErgoContract().getErgoTree().bytes(),ErgoValueT.ByteArray),
                ErgoAppKit.ergoValue(req.proxyNFT, ErgoValueT.ByteArrayFromHex)
            ],
            contract=appKit.contractFromTree(userProxyNFTLockedVestingContractTree)
        )
        logging.info("2")
        unsignedTx = appKit.buildUnsignedTransaction(
            inputs=userInputs,
            outputs=[proxyOutput],
            fee=int(1e6),
            sendChangeTo=Address.create(req.address).getErgoAddress()
        )

        if req.txFormat == TXFormat.EIP_12:
            return ErgoAppKit.unsignedTxToJson(unsignedTx)

        if req.txFormat == TXFormat.ERGO_PAY:
            reducedTx = appKit.reducedTx(unsignedTx)
            ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                reducedTx,
                address=req.address
            )
            cache.set(f'ergopay_signing_request_{unsignedTx.getId()}',ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{unsignedTx.getId()}'}

    except Exception as e:
        # return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Uncaught error: {e}')
        content = 'Unable to process transaction, please try again.'
        m = re.search('\(org.ergoplatform.appkit.ErgoClientException: Cannot load UTXO box (.+?)\)', str(e))
        if m is not None:
            content = f'Blockchain is synchronizing, please try again shortly (ref: {m.group(1)})'
        logging.error(f'ERR:{myself()}: {content} ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)

@r.post('/vestFromProxy', name="vesting:vestFromProxy")
async def vestFromProxy(req: VestFromProxyRequest):
    try:
        oracleInfo = getUnspentBoxesByTokenId(ergUsdOracleNFT)[0]
        #oracleInfo = getNFTBox(ergUsdOracleNFT,includeMempool=False)
        if oracleInfo is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failed to retrieve oracle box')
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
        nErgPerUSD = int(oracleInfo["additionalRegisters"]["R4"]["renderedValue"])
        sigUsdDecimals = int(2)
        sigUsdTokens = int(req.sigUSDAmount*10**sigUsdDecimals)
        whitelistTokens = int(req.vestingAmount*10**vestedTokenInfo["decimals"])
        requiredSigUSDTokens = int(whitelistTokens*priceNum/priceDenom)
        nergRequired = int((requiredSigUSDTokens-sigUsdTokens)*(nErgPerUSD*10**(-1*sigUsdDecimals)))
        userInputs = List[InputBox]
        tokensToSpend = {whitelistTokenId: whitelistTokens}
        if req.sigUSDAmount>0:
            tokensToSpend[sigusd] = sigUsdTokens
        if len(req.utxos) == 0:
            if len(req.addresses) == 0:
                userInputs = appKit.boxesToSpend(req.address,int(20e6+nergRequired),tokensToSpend)
            else:
                userInputs = appKit.boxesToSpendFromList(req.addresses,int(20e6+nergRequired),tokensToSpend)
        else:
            userInputs = appKit.getBoxesById(req.utxos)
            if not ErgoAppKit.boxesCovered(userInputs,int(20e6+nergRequired),tokensToSpend):
                userInputs = appKit.boxesToSpend(req.address,int(20e6+nergRequired),tokensToSpend)
        if userInputs is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not find enough erg and/or tokens')

        try:
            inputs = list(appKit.getBoxesById([proxyBox["boxId"]])) + list(userInputs)
        except ErgoClientException:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Not all input boxes could be found, try again in a few minutes')
        try:
            dataInputs = list(appKit.getBoxesById([oracleInfo["boxId"]]))
        except ErgoClientException:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Oracle box could not be found, try again in a few minutes')
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
                ErgoAppKit.ergoValue([
                    roundParameters[0],
                    roundParameters[1],
                    roundParameters[2],
                    whitelistTokens
                ],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(proxyBox["boxId"],ErgoValueT.ByteArrayFromHex)
            ],
            contract=appKit.contractFromTree(nftLockedVestingContractTree)
        )
        userOutput = appKit.mintToken(
            value=int(1e6),
            tokenId=proxyBox["boxId"],
            tokenName=f"{roundInfo['name']} Vesting Key",
            tokenDesc=f'{{"Vesting Round": "{roundInfo["name"]}", "Vesting start": "{datetime.fromtimestamp(roundParameters[2]/1000)}", "Periods": {roundParameters[1]}, "Period length": "{timedelta(milliseconds=roundParameters[0]).days} day(s)", "Total vested": {req.vestingAmount} }}',
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
            fee=int(17e6),
            sendChangeTo=Address.create(req.address).getErgoAddress()
        )

        if req.txFormat == TXFormat.EIP_12:
            return ErgoAppKit.unsignedTxToJson(unsignedTx)

        if req.txFormat == TXFormat.ERGO_PAY:
            reducedTx = appKit.reducedTx(unsignedTx)
            ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                reducedTx,
                address=req.address
            )
            cache.set(f'ergopay_signing_request_{unsignedTx.getId()}',ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{unsignedTx.getId()}'}

    except Exception as e:
        # return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Uncaught error: {e}')
        content = 'Unable to process transaction, please try again.'
        m = re.search('\(org.ergoplatform.appkit.ErgoClientException: Cannot load UTXO box (.+?)\)', str(e))
        if m is not None:
            content = f'Blockchain is synchronizing, please try again shortly (ref: {m.group(1)})'
        logging.error(f'ERR:{myself()}: {content} ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)


