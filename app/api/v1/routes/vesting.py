import requests, json, os
import fractions
import re

from decimal import Decimal
from sqlalchemy import create_engine, text
from starlette.responses import JSONResponse
from api.v1.routes.staking import AddressList
from core.auth import get_current_active_superuser 
from db.session import engDanaides 
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
@r.post("/v1/", name="vesting:v1")
def vestingV1(req: AddressList):
    try:
        userWallets = [Wallet(address) for address in req.addresses]
        userErgoTrees = [wallet.ergoTree() for wallet in userWallets]
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
                where right(v.r4, length(v.r4)-4) in ('{"','".join(userErgoTrees)}')
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
def redeemWithNFT(req: RedeemWithNFTRequest):
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
            return {'url': f'ergopay://api.ergopad.io/blockchain/signingRequest/{unsignedTx.getId()}'}

    except Exception as e:
        content = f'Unable to redeem currently. Please try again shortly or contact us in TG/Discord.'
        # found match with "reason"
        m = re.search('reason: NotEnoughErgsError\(not enough boxes to meet ERG needs (\d+) \(found only (\d+)\),\d+\)\)', str(e))
        if m is not None:
             content = f'transaction requires {(m.group(0)/10e9):,.3} ergs, and only {(m.group(1)/10e9):,.3} ergs were found.'
        logging.error(f'ERR:{myself()}: {content} ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)

# replacement for vestedWithNFT
@r.post("/v2/", name="vesting:v2")
def vestingV2(req: AddressList):
    try:
        sql = f'''
            select v.box_id
                , v.vesting_key_id
                , v.parameters
                , v.token_id
                , v.remaining
                , v.address
                , v.ergo_tree
                , t.token_name
                , t.decimals
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
                'Remaining': round(float(box['remaining'])*10**(-1*box['decimals']),box['decimals']),
                'Redeemable': round(redeemableTokens*10**(-1*box['decimals']),box['decimals']),
                'Vesting Key Id': box['vesting_key_id'],
                'Next unlock': datetime.fromtimestamp((vestingStart+((periods+1)*redeemPeriod))/1000)
            })

        return vested

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to build vesting request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to build vesting request.')

@r.get("/vestedWithKey/{key}", name="vesting:vestedWithKey")
def vestedWithKey(key: str):
    try:
        # find vesting tokens
        vested = {}
        sql = f'''
            select 
                  v.box_id
                , v.ergo_tree
                , v.remaining
                , v.vesting_key_id
                , v.parameters
                , t.token_name
                , t.decimals
                , u.assets[v.token_id] as redeemed
            from vesting v
                join tokens t on t.token_id = v.token_id
                join utxos u on u.box_id = v.box_id
            where v.vesting_key_id = %s
        '''
        with engDanaides.begin() as con:
            res = con.execute(sql, (key,)).fetchall()

        # no vesting for key
        if res is None:
            return vested

        # parse vesting row
        for row in res:
            if row['token_name'] not in vested:
                vested[row['token_name']] = []

            # parse params
            parameters = ErgoAppKit.deserializeLongArray(row['parameters'])            
            blockTime           = int(time()*1000)
            redeemPeriod        = parameters[0]
            numberOfPeriods     = parameters[1]
            vestingStart        = parameters[2]
            totalVested         = parameters[3]
            timeVested          = blockTime - vestingStart
            periods             = max(0, int(timeVested/redeemPeriod))
            redeemed            = totalVested - int(row['redeemed'])
            if row['ergo_tree'] == '1012040204000404040004020406040c0408040a050004000402040204000400040404000400d812d601b2a4730000d602e4c6a7050ed603b2db6308a7730100d6048c720302d605db6903db6503fed606e4c6a70411d6079d997205b27206730200b27206730300d608b27206730400d609b27206730500d60a9972097204d60b95917205b272067306009d9c7209b27206730700b272067308007309d60c959272077208997209720a999a9d9c7207997209720b7208720b720ad60d937204720cd60e95720db2a5730a00b2a5730b00d60fdb6308720ed610b2720f730c00d6118c720301d612b2a5730d00d1eded96830201aedb63087201d901134d0e938c721301720293c5b2a4730e00c5a79683050193c2720ec2720193b1720f730f938cb2720f731000017202938c7210017211938c721002720cec720dd801d613b2db630872127311009683060193c17212c1a793c27212c2a7938c7213017211938c721302997204720c93e4c67212050e720293e4c6721204117206':
                tgeNum              = parameters[4]
                tgeDenom            = parameters[5]
                tgeTime             = parameters[6]
                tgeAmount           = int(totalVested * tgeNum / tgeDenom) if (blockTime > tgeTime) else 0
                totalRedeemable     = int(periods * (totalVested-tgeAmount) / numberOfPeriods) + tgeAmount
            else:
                totalRedeemable     = int(periods * totalVested / numberOfPeriods)

            redeemableTokens = totalVested - redeemed if (periods >= numberOfPeriods) else totalRedeemable - redeemed
            decimals = row['decimals']
            vested[row['token_name']].append({
                'boxId': row['box_id'],
                'Remaining': round(row['remaining']/(10**decimals), decimals),
                'Redeemable': round(redeemableTokens/(10**decimals), decimals),
                'Vesting Key Id': row['vesting_key_id'],
                'Next unlock': datetime.fromtimestamp((vestingStart+((periods+1)*redeemPeriod))/1000)
            })

        return vested

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to vest with NFT.')

@r.post("/vestedWithNFT/", name="vesting:vestedWithNFT")
def vested(req: AddressList):
    try:
        # find vesting tokens
        vested = {}
        wallet_addresses = "'"+("','".join(req.addresses))+"'"
        sql = f'''
            select 
                  v.box_id
                , v.ergo_tree
                , v.remaining
                , v.vesting_key_id
                , v.parameters
                , t.token_name
                , t.decimals
                , u.assets[v.token_id] as redeemed
            from vesting v
                join tokens t on t.token_id = v.token_id
                join utxos u on u.box_id = v.box_id
            where v.address in ({wallet_addresses})
        '''
        with engDanaides.begin() as con:
            res = con.execute(sql).fetchall()

        # no vesting for address(es)
        if res is None:
            return vested

        # parse vesting row
        for row in res:
            if row['token_name'] not in vested:
                vested[row['token_name']] = []

            # parse params
            parameters = ErgoAppKit.deserializeLongArray(row['parameters'])            
            blockTime           = int(time()*1000)
            redeemPeriod        = parameters[0]
            numberOfPeriods     = parameters[1]
            vestingStart        = parameters[2]
            totalVested         = parameters[3]
            timeVested          = blockTime - vestingStart
            periods             = max(0, int(timeVested/redeemPeriod))
            redeemed            = totalVested - int(row['redeemed'])
            if row['ergo_tree'] == '1012040204000404040004020406040c0408040a050004000402040204000400040404000400d812d601b2a4730000d602e4c6a7050ed603b2db6308a7730100d6048c720302d605db6903db6503fed606e4c6a70411d6079d997205b27206730200b27206730300d608b27206730400d609b27206730500d60a9972097204d60b95917205b272067306009d9c7209b27206730700b272067308007309d60c959272077208997209720a999a9d9c7207997209720b7208720b720ad60d937204720cd60e95720db2a5730a00b2a5730b00d60fdb6308720ed610b2720f730c00d6118c720301d612b2a5730d00d1eded96830201aedb63087201d901134d0e938c721301720293c5b2a4730e00c5a79683050193c2720ec2720193b1720f730f938cb2720f731000017202938c7210017211938c721002720cec720dd801d613b2db630872127311009683060193c17212c1a793c27212c2a7938c7213017211938c721302997204720c93e4c67212050e720293e4c6721204117206':
                tgeNum              = parameters[4]
                tgeDenom            = parameters[5]
                tgeTime             = parameters[6]
                tgeAmount           = int(totalVested * tgeNum / tgeDenom) if (blockTime > tgeTime) else 0
                totalRedeemable     = int(periods * (totalVested-tgeAmount) / numberOfPeriods) + tgeAmount
            else:
                totalRedeemable     = int(periods * totalVested / numberOfPeriods)

            redeemableTokens = totalVested - redeemed if (periods >= numberOfPeriods) else totalRedeemable - redeemed
            decimals = row['decimals']
            vested[row['token_name']].append({
                'boxId': row['box_id'],
                'Remaining': round(row['remaining']/(10**decimals), decimals),
                'Redeemable': round(redeemableTokens/(10**decimals), decimals),
                'Vesting Key Id': row['vesting_key_id'],
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
def bootstrapRound(
    req: BootstrapRoundRequest, 
    current_user=Depends(get_current_active_superuser)
):
    try:
        logging.debug('bootstrapRound:getTokenInfo')
        vestedToken = getTokenInfo(req.tokenId)
        vestedTokenAmount = int(req.roundAllocation*10**vestedToken["decimals"])

        logging.debug('bootstrapRound:appKit')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/",CFG.ergopadApiKey)

        logging.debug('bootstrapRound:ergoPadContract')
        ergoPadContract = appKit.contractFromAddress(CFG.ergopadWallet)
        sellerContract = appKit.contractFromAddress(req.sellerAddress)

        logging.debug('bootstrapRound:initialInputs')
        initialInputs = appKit.boxesToSpend(CFG.ergopadWallet, int(5e6), {req.tokenId: vestedTokenAmount})

        logging.debug('bootstrapRound:nftId')
        nftId = initialInputs[0].getId().toString()

        logging.debug('bootstrapRound:presaleRoundNFTBox')
        presaleRoundNFTBox = appKit.mintToken(
            value=int(1e6),
            tokenId=nftId,
            tokenName=f"{req.roundName}",
            tokenDesc="NFT identifying the presale round box",
            mintAmount=1,
            decimals=0,
            contract=ergoPadContract
        )
        logging.debug('bootstrapRound:tokenBox')
        tokenBox = appKit.buildOutBox(
            value = int(3e6),
            tokens = {req.tokenId: vestedTokenAmount},
            registers = None,
            contract=ergoPadContract
        )

        logging.debug('bootstrapRound:nftMintUnsignedTx')
        nftMintUnsignedTx = appKit.buildUnsignedTransaction(
            inputs=initialInputs,
            outputs=[presaleRoundNFTBox,tokenBox],
            fee=int(1e6),
            sendChangeTo=ergoPadContract.toAddress().getErgoAddress()
        )

        logging.debug('bootstrapRound:nftMintSignedTx')
        nftMintSignedTx = appKit.signTransactionWithNode(nftMintUnsignedTx)

        logging.debug('bootstrapRound:sendTransaction')
        appKit.sendTransaction(nftMintSignedTx)

        logging.debug('bootstrapRound:whitelistTokenId')
        whitelistTokenId = nftMintSignedTx.getOutputsToSpend()[0].getId().toString()

        logging.debug('bootstrapRound:whiteListTokenBox')
        whiteListTokenBox = appKit.mintToken(
            value=int(1e6),
            tokenId=whitelistTokenId,
            tokenName=f"{req.roundName} whitelist token",
            tokenDesc=f"Token proving allocation for the {req.roundName} round",
            mintAmount=int(vestedTokenAmount*req.whitelistTokenMultiplier),
            decimals=vestedToken["decimals"],
            contract=ergoPadContract
        )

        sigusd = "03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04"
        ergusdoracle = "011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"

        logging.debug('bootstrapRound:NFTLockedVestingV2')
        with open(f'contracts/NFTLockedVestingV2.es') as f:
            script = f.read()
        nftLockedVestingContractTree = appKit.compileErgoScript(script)

        logging.debug('bootstrapRound:proxyNFTLockedVestingV2')
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

        logging.debug('bootstrapRound:price')
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

        logging.debug('bootstrapRound:buildUnsignedTransaction')
        bootstrapUnsigned = appKit.buildUnsignedTransaction(
            inputs=[nftMintSignedTx.getOutputsToSpend()[0],nftMintSignedTx.getOutputsToSpend()[1]],
            outputs=[whiteListTokenBox,proxyContractBox],
            fee=int(1e6),
            sendChangeTo=ergoPadContract.toAddress().getErgoAddress()
        )

        logging.debug('bootstrapRound:bootstrapSigned')
        bootstrapSigned = appKit.signTransactionWithNode(bootstrapUnsigned)

        logging.debug('bootstrapRound:sendTransaction')
        appKit.sendTransaction(bootstrapSigned)

        logging.debug('bootstrapRound:return')
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
def activeRounds():
    try:
        result = {'activeRounds': [], 'soldOutRounds': []}
        sql = f'''
            with prx as (
                select id, box_id, registers::json, transaction_id, height
                    , (each(assets)).key as k
                    , (each(assets)).value::bigint as qty
                from utxos u
                where ergo_tree in (
                    -- Jf7SDZuaVDGiCwCxC7N2y8cuptH3cgNT1nteJK469effW2gNarYn1AxsYjNcP7zYtvzmVjNPMmE3PYJRMC2E7m3yTDBrHvv8voJM35a9ktLb3bNeQ4qEJSyFse3pQeqcTxvPATNAv7RHc3fnAkBf3PsNBGFoRq2nwnciNwUaNcunyfWz2JDbwrBzMT7gMfs8U9YKAKGU1V754PUa1WRccaUfWxDAj5zVVkzkvVNNeQPH2g9GAu539Kc5792XLRwfv5MqaBkQ6KqHw8tgck2e55G4sY6n9ZQ4vboeuVC9JzsuiYraAuc6Lbj1NbPdDRaHXBUAQioDuzRBFxDFwLdmsZXykdvDfJZDytxPoCkzdfMmr8Zchga8vELSydrJ8smXbjWnrySGTZWqcQbJLB1YwPDiGVQvDvvQhRSezJcGMXUXea9zX6cCaeAsrqCULonZKVoeVgCNGte6VFk7PTKJ5W5LrRW1cgkJNRHYrpqPujPN8SoMgLjt1zvCKww5eSuu2RXqyZNVPRxMU3uQd3F2hRjGAmJA6M8Mz5QdZmoXj1LRWnrz1C1E6z6mL1Unry2GYWbxfTsVFRbZVZEv78yn9TUN7cuA163BSoxLVeKwUbGC2uiWeWSm1FzTPNCHHpVtBRfTACKoNbxag9SGgxpsepyxaF7snbXhKtBnqFvyg2ZEiiHXUDjY1Qy8kjf9JrdLmifU6WaZ7VdhNEdHGpf72ivo5sVPNEeUKoKfHAY6WWokivYjeSpKCSLjougKwaNoR79tUWdfN8CEudwUSebWXD92cbnMZxS7QBvGqcUSGRQuuD1uXgeWF8m76xgVH4sQfTuMMvYVWeH8e8bHHqtQMzw2FUajFo2F1mxxwVqvkUQJgmRQXYBndDGiquVCvTqNdZ25eo32gf
                    '1025040004060402040004020406040804020400040204040400040004000e20011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f040404020e2003faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf040500050005c801050005020400040004000580897a0e20891ed18c9e35ca9e77deb89b0231290649f542c9e205fa61d62c644c68700459040004000402050004040404040604020502d816d601b2db6501fe730000d602b2a5730100d603db63087202d604db6308a7d605b27204730200d606b2a5730300d607db63087206d608b27207730400d609998c7205028c720802d60ae4c6a70411d60b9d9c7209b2720a730500b2720a730600d60cc5a7d60de4c6a7050ed60ee4c6a7060ed60fe4c6a7070ed610b2a5730700d611b2db63087210730800d612e4c672100411d613b27212730900d614b2a5730a00d615b2db63087214730b00d616b27203730c00d196830601938cb2db63087201730d0001730e929a9593b17203730fd801d617b2720373100095938c72170173118c721702731273139d9cc172027314e4c6720104059591720b7315720b73169683090193720cc5b2a473170093c1a7c1720693c2a7c2720693b27204731800b27207731900938c7205018c72080193720ae4c67206041193720de4c67206050e93720ee4c67206060e93720fe4c67206070e96830a0193c17210731a93cbc27210731b938c721101720d938c721102720993b27212731c00b2720a731d00937213b2720a731e00917213731f93b27212732000b2720a73210093b27212732200720993e4c67210050e720c9683030193c27214c2b2a4732300938c721501720c938c72150273249683030193c27202720e938c721601720f938c7216027209'
                    -- 4qyzRyJzKPEYP9XSTWsXH6hzhMCH1rMx5JvcYpVwWpD79bLDex79Bj6hbLR1NnVVYFFLCGCTSGQDQTkh5dm5d2BQY5bQRpf1AycoDjAEZyQwxiLRpbwB8Kiqyi7mUvb5UcJRdtUQ6sqcDZpgyf3hBUCCy2vg8e8P3wSopzkensJ4SoG86upev1TXacBRqsm54dshaMdToMAyFBLD2DMsZPP89gEZF4UAuLbRxZDiK871fT1NVCwa7pWK29ySAipERxWwno112zQoF5a9htj37VavXkYTzcZQ24iVjrkrfxU12huR9ZPkvLHkrdu8y8WgFdFr5oKFMsm2teFCrXMx8n9MUEEymFSWhMXBvg5UAkKW5ido9Zo2BYWDj81ew5fUoWhdJGGCu33SegnLzbNiB6VaRNusiZSPwLBA2NZ5yF5UJrUnMZAqPqWZb7zZ2zL2cBwSrFJ7kxSrQeaJ1RNGcQiDyXmzDE9vpyWTbG9W1mW5KzzMD4B9FZoUcRYbmFdp31H5Ho27rTNfx64tr7Crgjm7WfWVp8zPXjxfjW6su6u2GK6cx3feavARGNjyKKrYW3H8yPFi1Y9ruwmNwTyW96Z42FE1D28VuD5C2SJYmegbg9nPKc3ByUbS5CHJQQ4DLX9DdgZvbtq44VsiR2VmbpZNrjMwEHybRcoiDeLNhoPqxinXNvFNjg9gSca1C47EiYy4S94eFqbY1rrcF84siSEUq31e9A6snNTcDEiQ3efCcEyCb1JgA5iLDU7kqoi6xxCt7TKVfA96EKSczjaqBk5jvrmAhZrDpwrKm1sSf8py21tUgbdyDoJccUdRniahbibSRc5PVpukkkKtAUXEDG91qNbbuh47QA2NjSMiqNQjYGNJTaiBBDsGbxXjwgFkJA45E9FaFzvMvGuJyKJY9Yx9e6KBoSq1ktY38WHkFe7PBLwyZxUowb4fmgexLKiUWfLNzoZhHYu8DuAkgRtVoPRQxZYrqdgkg4PwAF6AE7XHVJEUr6iQHwTWVkp9LajbPXKtFQmVpnFNowcVVrVSabX5aqAmEu1PKVKJjvLwumUwoyRi6NwMqudVKAEqP3vdtmqr1KWzs9mNqgAybP8qaUM9pif9CxTGUKPR5FEsgnJv3WwvdJwbYv2J
                    , '103404020e205a50f4348840095fed4e84f94c6f1c0b540cc41d5c4dfc8b1f483e9c72315ecd040004060400040604080400040204040400040004000e20011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f040404020e2003faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf040500050005c8010500050204000400040004020402040204020580897a010104000400040205000404040404060408040c040a040e040c041004020502040004000402040a04000400d804d601b2a5730000d602c27201d60393cb72027301d604e4c6a7060e957203d812d605b2db6501fe730200d606b2a5730300d607db63087206d608b2db63087201730400d6098c720802d60ae4c6a70411d60b9d9c7209b2720a730500b2720a730600d60cc5a7d60db2a5730700d60edb6308a7d60fdb6308720dd610e4c6a7050ed611e4c6a7070ed612e4c672010411d613b27212730800d614b2a5730900d615b2db63087214730a00d616b27207730b00d196830601938cb2db63087205730c0001730d929a9593b17207730ed801d617b27207730f0095938c72170173108c721702731173129d9cc172067313e4c6720504059591720b7314720b73159683090193720cc5b2a473160093c1a7c1720d93c2a7c2720d93b2720e731700b2720f7318009593b1720f7319938cb2720e731a00027209938cb2720f731b0002998cb2720e731c0002720993720ae4c6720d0411937210e4c6720d050e937204e4c6720d060e937211e4c6720d070e96830d0193c17201731d7203938c7208017210731e93b27212731f00b2720a732000937213b2720a732100917213732293b27212732300b2720a73240093b27212732500720993b27212732600b2720a73270093b27212732800b2720a73290093b27212732a00b2720a732b0093e4c67201050e720c9683030193c27214e4c6b2a4732c00050e938c721501720c938c721502732d9683030193c272067204938c7216017211938c7216027209d802d605db6308a7d606b2a5732e00d196830601937202720493c17201c1a793b2db63087201732f00b2720573300092db6903db6503feb2e4c6a7041173310093c27206c2a793b2db63087206733200b27205733300'
                )
            )
            -- remaining tokens and decimals
            , ar1 as (
                select prx.id, tok.token_name, tok.token_id, tok.decimals
                from prx
                join tokens tok on tok.token_id = k
                where prx.qty != 1
            )
            -- round name
            , ar2 as (
                select prx.id, tok.token_name, tok.token_id, null
                from prx
                join tokens tok on tok.token_id = k
                where prx.qty = 1
            )
            select prx.id, prx.box_id, prx.registers::json, prx.transaction_id, prx.k
                , ar2.token_id as proxy_nft 
                , prx.qty/power(10, ar1.decimals::int) as remaining
                , ar1.token_name
                , ar2.token_name as round_name
            from prx
                left join ar1 on ar1.id = prx.id
                left join ar2 on ar2.id = prx.id
            where prx.qty > 1
        '''
        with engDanaides.begin() as con:
            proxyBoxes = con.execute(sql).fetchall()

        for proxyBox in proxyBoxes:
            try:
                logging.info(f'''round: {proxyBox['round_name']}/{proxyBox["remaining"]}''')
                if proxyBox["remaining"] > 10.0:
                    result['activeRounds'].append({
                        'roundName': proxyBox["round_name"], 
                        'proxyNFT': proxyBox['proxy_nft'], 
                        'remaining': proxyBox["remaining"],
                        'Whitelist tokenId': proxyBox["registers"]['R7'][4:]
                    })
                else:
                    result['soldOutRounds'].append({
                        'roundName': proxyBox["round_name"], 
                        'proxyNFT': proxyBox["registers"]['R4']
                    })
            except Exception as e:
                logging.debug(e)
                pass
        
        return result

    except Exception as e:
        logging.error(f'ERR:{myself()}: Unable to determine proper round. ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to determine proper round.')

class RequiredNergTokensRequest(BaseModel):
    proxyNFT: str
    vestingAmount: Decimal
    sigUSDAmount: Decimal

@r.post('/requiredNergTokens', name="vesting:requiredNergTokens")
def requiredNergTokens(req: RequiredNergTokensRequest):
    try:
        proxyBox = getNFTBox(req.proxyNFT)
        whitelistTokenId = proxyBox["additionalRegisters"]["R7"]["renderedValue"]
        vestedTokenId = proxyBox["additionalRegisters"]["R5"]["renderedValue"]
        roundParameters = eval(proxyBox["additionalRegisters"]["R4"]["renderedValue"])
        priceNum = roundParameters[3]
        priceDenom = roundParameters[4]
        vestedTokenInfo = getTokenInfo(vestedTokenId)
        oracleInfo = ergusdoracle()
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
def contribute(req: VestFromProxyRequest):
    try:
        oracleInfo = ergusdoracle()
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
            return {'url': f'ergopay://api.ergopad.io/blockchain/signingRequest/{unsignedTx.getId()}'}

    except Exception as e:
        # return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Uncaught error: {e}')
        content = 'Unable to process transaction, please try again.'
        m = re.search('\(org.ergoplatform.appkit.ErgoClientException: Cannot load UTXO box (.+?)\)', str(e))
        if m is not None:
            content = f'Blockchain is synchronizing, please try again shortly (ref: {m.group(1)})'
        logging.error(f'ERR:{myself()}: {content} ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)

@r.post('/vestFromProxy', name="vesting:vestFromProxy")
def vestFromProxy(req: VestFromProxyRequest):
    content = 'this method is being replaced, please contact admin'
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)
