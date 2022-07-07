import requests, json, os
import fractions
import re

from decimal import Decimal
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
from api.v1.routes.blockchain import TXFormat, ergusdoracle, getNFTBox, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens, getUnspentBoxesByTokenId
from hashlib import blake2b
from cache.cache import cache
from ergo_python_appkit.appkit import ErgoAppKit, ErgoValueT, ErgoValue
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
async def redeemToken(address:str, numBoxes:Optional[int]=200):
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
                try: 
                    assert 'R5' in box['additionalRegisters']
                    # logging.warning(f'''REDEEM 1: {box['index']}''')
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

                except Exception as e:
                    logging.warning(f'missing R5 from box: {box}')
                    pass

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
@r.get("/v1/{wallet}", name="vesting:v1")
async def vestingV1(wallet:str):
    try:
        userWallet = Wallet(wallet)
        userErgoTree = userWallet.ergoTree()
        engDanaides = create_engine(CFG.csDanaides)
        sql = f'''
            with v as (
                    select id 
                        , ergo_tree
                        , box_id
                        , registers->'R4' as r4
						, registers->'R5' as r5
						, registers->'R6' as r6
						, registers->'R7' as r7
						, registers->'R8' as r8
                        , (each(assets)).key::varchar(64) as token_id
                        , (each(assets)).value as amount
                    from utxos
                    where ergo_tree = '10070400040204000500040004000400d80bd601e4c6a7040ed602b2db6308a7730000d6038c720201d604e4c6a70805d605e4c6a70705d606e4c6a70505d607e4c6a70605d6089c9d99db6903db6503fe720572067207d6098c720202d60a9972047209d60b958f99720472087207997204720a997208720ad1ed93b0b5a5d9010c63ededed93c2720c720193e4c6720c040ee4c6a7090e93b1db6308720c7301938cb2db6308720c7302000172037303d9010c41639a8c720c018cb2db63088c720c0273040002720bec937209720baea5d9010c63ededededededededed93c1720cc1a793c2720cc2a7938cb2db6308720c730500017203938cb2db6308720c73060002997209720b93e4c6720c040e720193e4c6720c0505720693e4c6720c0605720793e4c6720c0705720593e4c6720c0805720493e4c6720c090ee4c6a7090e'
                )
				select v.box_id
					, v.r4, v.r5, v.r6, v.r7, v.r8
					, v.token_id::varchar(64)
					, v.amount::bigint -- need to divide by decimals
					, v.ergo_tree::text
                    , t.token_name
                    , t.decimals
				from v
					-- filter to only vesting keys
					-- join assets a on a.token_id = v.vesting_key_id    
                    join tokens t on t.token_id = v.token_id 
                where right(v.r4, length(v.r4)-4) = {userErgoTree!r}
        '''
        with engDanaides.begin() as con:
            boxes = con.execute(sql).fetchall()

        result = {}
        for box in boxes:
            logging.debug(f'''token: {box['token_name']}''')
            r5 = ErgoValue.fromHex(box["r5"]).getValue()
            r6 = ErgoValue.fromHex(box["r6"]).getValue()
            r7 = ErgoValue.fromHex(box["r7"]).getValue()
            r8 = ErgoValue.fromHex(box["r8"]).getValue()
            tokenId = box["token_id"]
            if tokenId not in result:
                result[tokenId] = {
                    'name': box["token_name"],
                    'totalVested': 0.0,
                    'outstanding': {},
                }
            tokenDecimals = 10**box["decimals"]
            initialVestedAmount = int(r8)/tokenDecimals
            nextRedeemAmount = int(r6)/tokenDecimals
            remainingVested = int(box["amount"])/tokenDecimals
            result[tokenId]['totalVested'] += remainingVested
            nextRedeemTimestamp = (((initialVestedAmount-remainingVested)/nextRedeemAmount+1)*int(r5)+int(r7))/1000.0
            nextRedeemDate = date.fromtimestamp(nextRedeemTimestamp)
            logging.debug(nextRedeemDate)
            while remainingVested > 0:
                if nextRedeemDate not in result[tokenId]['outstanding']:
                    result[tokenId]['outstanding'][nextRedeemDate] = {}
                    result[tokenId]['outstanding'][nextRedeemDate]['amount'] = 0.0
                redeemAmount = nextRedeemAmount if remainingVested >= 2*nextRedeemAmount else remainingVested
                result[tokenId]['outstanding'][nextRedeemDate]['amount'] += round(redeemAmount, int(box["decimals"]))
                remainingVested -= redeemAmount
                nextRedeemTimestamp += int(r5)/1000.0
                nextRedeemDate = date.fromtimestamp(nextRedeemTimestamp)        
                logging.debug(nextRedeemDate)

        return result

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to build ergopad vesting request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to build ergopad vesting request.')

# find vesting/vested tokens
@r.get("/vested/{wallet}", name="vesting:findVestedTokens")
async def findVestingTokens(wallet:str):
    CACHE_TTL = 3600 # 60 mins (this is only changed once per month)
    try:
        # check cache first
        cached = cache.get(f"get_vesting_vested_ergopad_{wallet}")
        if cached:
            return cached
        # tokenId = CFG.ergopadTokenId
        total = 0
        result = {}
        userWallet = Wallet(wallet)
        userErgoTree = userWallet.ergoTree()
        address = CFG.vestingContract
        offset = 0
        res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers))
        while res.ok:
            # returns array of dicts
            for box in res.json()["items"]:
                try: 
                    assert "R4" in box["additionalRegisters"]
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
                except Exception as e:
                    logging.debug(f'VESTED: Missing R4 key in box: {box}')
                    pass
            if len(res.json()['items']) == 500:
                offset += 500
                res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={0}&limit=500', headers=dict(headers))
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
                tokenResult['outstanding'].append({'date': str(redeemDate), 'amount': value['outstanding'][redeemDate]['amount']})
            resJson.append(tokenResult)

        ret = {
            'status': 'success',
            'vested': resJson
        }
        cache.set(f"get_vesting_vested_ergopad_{wallet}", ret, CACHE_TTL)
        return ret

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to build vesting request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to build vesting request.')

@r.get('/unspent', name="vesting:unspent")
async def getUnspentExchange(tokenId=CFG.ergopadTokenId, allowMempool=True):
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

# replacement for vestedWithNFT
@r.post("/v2/", name="vesting:v2")
async def vestingV2(req: AddressList):
    try:
        engDanaides = create_engine(CFG.csDanaides)
        sql = f'''
            select v.box_id, v.vesting_key_id, v.parameters, v.token_id, v.remaining, v.address, v.ergo_tree
                , t.token_name, t.decimals
            from vesting v 
                join tokens t on t.token_id = v.token_id
            where address in ('{"','".join(req.addresses)}')
        '''
        with engDanaides.begin() as con:
            boxes = con.execute(sql).fetchall()

        vested = {}
        for box in boxes:
            logging.debug(f'''box: {box['box_id']}''')
            # parse parameters
            parameters          = ErgoAppKit.deserializeLongArray(box['parameters'])
            blockTime           = int(time()*1000)
            redeemPeriod        = parameters[0]
            numberOfPeriods     = parameters[1]
            vestingStart        = parameters[2]
            totalVested         = parameters[3]
            timeVested          = blockTime - vestingStart
            periods             = max(0,int(timeVested/redeemPeriod))
            redeemed            = totalVested - int(box['remaining'])
            logging.debug(f'''redeemed: {redeemed}''')

            # handle extended parameters
            if box["ergo_tree"]  == "1012040204000404040004020406040c0408040a050004000402040204000400040404000400d812d601b2a4730000d602e4c6a7050ed603b2db6308a7730100d6048c720302d605db6903db6503fed606e4c6a70411d6079d997205b27206730200b27206730300d608b27206730400d609b27206730500d60a9972097204d60b95917205b272067306009d9c7209b27206730700b272067308007309d60c959272077208997209720a999a9d9c7207997209720b7208720b720ad60d937204720cd60e95720db2a5730a00b2a5730b00d60fdb6308720ed610b2720f730c00d6118c720301d612b2a5730d00d1eded96830201aedb63087201d901134d0e938c721301720293c5b2a4730e00c5a79683050193c2720ec2720193b1720f730f938cb2720f731000017202938c7210017211938c721002720cec720dd801d613b2db630872127311009683060193c17212c1a793c27212c2a7938c7213017211938c721302997204720c93e4c67212050e720293e4c6721204117206":
                tgeNum          = parameters[4]
                tgeDenom        = parameters[5]
                tgeTime         = parameters[6]
                tgeAmount       = int(totalVested * tgeNum / tgeDenom) if (blockTime > tgeTime) else 0
                totalRedeemable = int(periods * (totalVested-tgeAmount) / numberOfPeriods) + tgeAmount
            else:     
                totalRedeemable = int(periods * totalVested / numberOfPeriods)
            redeemableTokens    = totalVested - redeemed if (periods >= numberOfPeriods) else totalRedeemable - redeemed
            logging.debug(f'''redeemableTokens: {redeemableTokens}''')

            # build response
            logging.debug(f'''token name: {box['token_name']}''')
            if box['token_name'] not in vested:
                vested[box['token_name']] = []
            vested[box['token_name']].append({
                'boxId': box["box_id"],
                'Remaining': round(box['remaining']*10**(-1*box['decimals']),box['decimals']),
                'Redeemable': round(redeemableTokens*10**(-1*box['decimals']),box['decimals']),
                'Vesting Key Id': box['vesting_key_id'],
                'Next unlock': datetime.fromtimestamp((vestingStart+((periods+1)*redeemPeriod))/1000)
            })

        return vested

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to build vesting request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to build vesting request.')

@r.post("/vestedWithNFT/", name="vesting:vestedWithNFT")
async def vested(req: AddressList):
    CACHE_TTL = 1800 # 30 mins (invalidated by invalidation service on change)
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
            '4qyzRyJzKPEYP9XSTWsXH6hzhMCH1rMx5JvcYpVwWpD79bLDex79Bj6hbLR1NnVVYFFLCGCTSGQDQTkh5dm5d2BQY5bQRpf1AycoDjAEZyQwxiLRpbwB8Kiqyi7mUvb5UcJRdtUQ6sqcDZpgyf3hBUCCy2vg8e8P3wSopzkensJ4SoG86upev1TXacBRqsm54dshaMdToMAyFBLD2DMsZPP89gEZF4UAuLbRxZDiK871fT1NVCwa7pWK29ySAipERxWwno112zQoF5a9htj37VavXkYTzcZQ24iVjrkrfxU12huR9ZPkvLHkrdu8y8WgFdFr5oKFMsm2teFCrXMx8n9MUEEymFSWhMXBvg5UAkKW5ido9Zo2BYWDj81ew5fUoWhdJGGCu33SegnLzbNiB6VaRNusiZSPwLBA2NZ5yF5UJrUnMZAqPqWZb7zZ2zL2cBwSrFJ7kxSrQeaJ1RNGcQiDyXmzDE9vpyWTbG9W1mW5KzzMD4B9FZoUcRYbmFdp31H5Ho27rTNfx64tr7Crgjm7WfWVp8zPXjxfjW6su6u2GK6cx3feavARGNjyKKrYW3H8yPFi1Y9ruwmNwTyW96Z42FE1D28VuD5C2SJYmegbg9nPKc3ByUbS5CHJQQ4DLX9DdgZvbtq44VsiR2VmbpZNrjMwEHybRcoiDeLNhoPqxinXNvFNjg9gSca1C47EiYy4S94eFqbY1rrcF84siSEUq31e9A6snNTcDEiQ3efCcEyCb1JgA5iLDU7kqoi6xxCt7TKVfA96EKSczjaqBk5jvrmAhZrDpwrKm1sSf8py21tUgbdyDoJccUdRniahbibSRc5PVpukkkKtAUXEDG91qNbbuh47QA2NjSMiqNQjYGNJTaiBBDsGbxXjwgFkJA45E9FaFzvMvGuJyKJY9Yx9e6KBoSq1ktY38WHkFe7PBLwyZxUowb4fmgexLKiUWfLNzoZhHYu8DuAkgRtVoPRQxZYrqdgkg4PwAF6AE7XHVJEUr6iQHwTWVkp9LajbPXKtFQmVpnFNowcVVrVSabX5aqAmEu1PKVKJjvLwumUwoyRi6NwMqudVKAEqP3vdtmqr1KWzs9mNqgAybP8qaUM9pif9CxTGUKPR5FEsgnJv3WwvdJwbYv2J']
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
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
        nErgPerUSD = int(oracleInfo["latest_datapoint"]*1.01)
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
        nergRequired = max(int((requiredSigUSDTokens-sigUsdTokens)*(nErgPerUSD*10**(-1*sigUsdDecimals))),int(0))
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


