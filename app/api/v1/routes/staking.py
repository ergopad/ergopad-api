import requests
import asyncio

from starlette.responses import JSONResponse
from wallet import Wallet
from config import Config, Network # api specific config
from fastapi import APIRouter, Request, Depends, Response, encoders, status
from typing import List
from pydantic import BaseModel
from time import sleep, time
from datetime import datetime
from base64 import b64encode
from ergo.util import encodeLongArray, encodeString, hexstringToB64
from hashlib import blake2b
from api.v1.routes.blockchain import TXFormat, getInputBoxes, getNFTBox, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens, getUnspentStakeBoxes
from db.session import get_db
from db.crud.staking_config import get_all_staking_config, get_staking_config_by_name, create_staking_config, edit_staking_config, delete_staking_config
from db.schemas.stakingConfig import StakingConfig, CreateAndUpdateStakingConfig
from core.auth import get_current_active_superuser, get_current_active_user
from core.security import get_md5_hash
from cache.staking import AsyncSnapshotEngine
from cache.cache import cache

from ergo_python_appkit.appkit import ErgoAppKit, ErgoValueT
from org.ergoplatform.appkit import Address, ErgoValue, OutBox, InputBox

from paideia_contracts.contracts.staking import CreateAddStakeProxyTransaction, CreateStakeProxyTransaction, CreateUnstakeProxyTransaction, PaideiaConfig, PaideiaTestConfig

stakingConfigs = {
    'paideiatest': PaideiaTestConfig,
    'paideia': PaideiaConfig
}

staking_router = r = APIRouter()

#region INIT
CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

CFG["stakeStateNFT"] = "05cde13424a7972fbcd0b43fccbb5e501b1f75302175178fc86d8f243f3f3125"
CFG["stakePoolNFT"] = "0d01f2f0b3254b4a1731e1b61ad77641fe54de2bd68d1c6fc1ae4e7e9ddfb212"
CFG["emissionNFT"] = "0549ea3374a36b7a22a803766af732e61798463c3332c5f6d86c8ab9195eed59"
CFG["stakeTokenID"] =  "1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee"
CFG["stakedTokenID"] = "d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413"

nergsPerErg = 10**9
headers = {'Content-Type': 'application/json'}

week = 1000*60*60*24*7
duration_ms = {
    'month': 365*24*60*60*1000/12,
    'week': week,
    'day': 24*60*60*1000,
    'minute': 60*1000
}
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region CLASSES
class UnstakeRequest(BaseModel):
    stakeBox: str
    amount: float
    address: str = ""
    utxos: List[str]
    txFormat: TXFormat
    addresses: List[str] = []

class AddressList(BaseModel):
    addresses: List[str]

class APIKeyRequest(BaseModel):
    apiKey: str
    numBoxes: int = 25

class StakeRequest(BaseModel):
    wallet: str
    amount: float
    utxos: List[str]
    txFormat: TXFormat
    addresses: List[str] = []

class BootstrapRequest(BaseModel):
    stakeStateNFT: str
    stakePoolNFT: str
    emissionNFT: str
    stakeTokenID: str
    stakedTokenID: str
    stakeAmount: int
    emissionAmount: int
    cycleDuration_ms: int
#endregion CLASSES

@r.post("/unstake/", name="staking:unstake")
async def unstake(req: UnstakeRequest):
    try:
        logging.debug('unstake::appKit')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)

        logging.debug('unstake::get NFT stakeStateBox')
        stakeStateBox = getNFTBox(CFG.stakeStateNFT)
        if stakeStateBox is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to find stake state box')
        res = requests.get(f'{CFG.explorer}/boxes/{req.stakeBox}')

        if res.ok:
            logging.debug('unstake::find stakeBox')
            stakeBox = res.json()
            currentTime = int(time()*1000)
            amountToUnstake = min(int(req.amount*10**2),stakeBox["assets"][1]["amount"])
            remaining = stakeBox["assets"][1]["amount"]-amountToUnstake
            logging.debug(f'unstake::find remaining=={remaining}')
            if remaining > 0 and remaining < 1000:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Remaining amount needs to be at least 10 ErgoPad')
            stakeBoxR4 = eval(stakeBox["additionalRegisters"]["R4"]["renderedValue"])
            stakeTime = stakeBoxR4[1] 
            
            logging.debug('unstake::get NFG userBox')
            userBox = getNFTBox(stakeBox["additionalRegisters"]["R5"]["renderedValue"])
            timeStaked = currentTime - stakeTime
            weeksStaked = int(timeStaked/week)
            penalty = int(0 if (weeksStaked >= 8) else amountToUnstake*5/100  if (weeksStaked >= 6) else amountToUnstake*125/1000 if (weeksStaked >= 4) else amountToUnstake*20/100 if (weeksStaked >= 2) else amountToUnstake*25/100)
            partial = amountToUnstake < stakeBox["assets"][1]["amount"]

            logging.debug('unstake::stake state R4')
            stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
            if stakeStateR4[1] != stakeBoxR4[0]:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'This stake box has a pending compound transaction. Compounding needs to happen before unstaking.')
            
            logging.debug('unstake::build outBox 1')
            outputs = []
            outputs.append(appKit.buildOutBox(
                value = stakeStateBox["value"],
                tokens={
                    CFG.stakeStateNFT: 1,
                    CFG.stakeTokenID: (stakeStateBox["assets"][1]["amount"] if (partial) else stakeStateBox["assets"][1]["amount"]+1)
                },
                registers=[
                    ErgoAppKit.ergoValue([
                        int(stakeStateR4[0]-amountToUnstake),
                        int(stakeStateR4[1]),
                        int(stakeStateR4[2] - (0 if (partial) else 1)),
                        int(stakeStateR4[3]),
                        int(stakeStateR4[4])], ErgoValueT.LongArray)
                ],
                contract=appKit.contractFromAddress(stakeStateBox["address"])
            ))
               
            logging.debug('unstake::build outBox 2')
            outputs.append(appKit.buildOutBox(
                value=int(0.01*nergsPerErg),
                tokens={CFG.stakedTokenID:amountToUnstake-penalty,stakeBox["additionalRegisters"]["R5"]["renderedValue"]:1} if (partial) else {CFG.stakedTokenID:amountToUnstake-penalty},
                registers=None,
                contract=appKit.contractFromAddress(userBox["address"])
            ))
                
            try: logging.debug(f'unstake::partial=={partial}')
            except: pass
            assetsToBurn = {}
            if partial:
                outputs.append(appKit.buildOutBox(
                    value = stakeBox["value"],
                    tokens = {
                        CFG.stakeTokenID: 1,
                        CFG.stakedTokenID: stakeBox["assets"][1]["amount"]-amountToUnstake
                    },
                    registers=[
                        ErgoValue.fromHex(stakeBox["additionalRegisters"]["R4"]["serializedValue"]),
                        ErgoValue.fromHex(stakeBox["additionalRegisters"]["R5"]["serializedValue"])
                    ],
                    contract=appKit.contractFromAddress(stakeBox["address"])
                ))
            else:
                assetsToBurn[stakeBox["additionalRegisters"]["R5"]["renderedValue"]] = 1
            if penalty > 0:
                assetsToBurn[CFG.stakedTokenID] = penalty

            logging.debug('unstake::address')
            if req.address == "":
                changeAddress = userBox["address"]
            else:
                changeAddress = req.address

            userInputs = List[InputBox]
            tokensToSpend = {stakeBox["additionalRegisters"]["R5"]["renderedValue"]:1}

            logging.debug('unstake::count utxos')
            if len(req.utxos) == 0:
                if len(req.addresses) == 0:
                    userInputs = appKit.boxesToSpend(req.address,int(2e7),tokensToSpend)
                else:
                    userInputs = appKit.boxesToSpendFromList(req.addresses,int(2e7),tokensToSpend)
            else:
                userInputs = appKit.getBoxesById(req.utxos)
                if not ErgoAppKit.boxesCovered(userInputs,int(2e7),tokensToSpend):
                    userInputs = appKit.boxesToSpend(req.address,int(2e7),tokensToSpend)
            if userInputs is None:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not find enough erg and/or tokens')

            keyBox = None
            otherBoxes = []

            logging.debug('unstake::each user input')
            for box in userInputs:
                keyFound = False
                for token in box.getTokens():
                    if token.getId().toString() == stakeBox["additionalRegisters"]["R5"]["renderedValue"]:
                        keyBox = box
                        keyFound=True
                if not keyFound:
                    otherBoxes.append(box)

            logging.debug('unstake::other boxes')
            userInputs = [keyBox] + list(otherBoxes)

            userInputs = ErgoAppKit.cutOffExcessUTXOs(userInputs,int(2e7),{stakeBox["additionalRegisters"]["R5"]["renderedValue"]:1})
            
            inputs = appKit.getBoxesById([stakeStateBox["boxId"],req.stakeBox])

            unsignedTx = appKit.buildUnsignedTransaction(inputs+userInputs,outputs,int(1e6),Address.create(changeAddress).getErgoAddress(),tokensToBurn=assetsToBurn)
            
            logging.debug('unstake::txFormat')
            if req.txFormat == TXFormat.EIP_12:
                logging.debug('unstake::EIP_12')
                result = {
                    'penalty': (penalty/100),
                    'unsignedTX': ErgoAppKit.unsignedTxToJson(unsignedTx)
                }

                return result

            if req.txFormat == TXFormat.ERGO_PAY:
                logging.debug('unstake::ERGO_PAY')
                reducedTx = appKit.reducedTx(unsignedTx)
                ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                    reducedTx,
                    address=changeAddress
                )
                cache.set(f'ergopay_signing_request_{unsignedTx.getId()}',ergoPaySigningRequest)
                return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{unsignedTx.getId()}'}
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to fetch stake box')

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to unstake, try again shortly or contact support if error continues.')

@r.get("/snapshot/", name="staking:snapshot")
def snapshot(
    request: Request,
    current_user=Depends(get_current_active_user)
):
    try:
        # Faster API Calls
        engine = AsyncSnapshotEngine()

        checkBoxes = getUnspentStakeBoxes()
        for box in checkBoxes:
            if box["assets"][0]["tokenId"] == CFG.stakeTokenID:
                tokenId = box["additionalRegisters"]["R5"]["renderedValue"]
                amount = int(box["assets"][1]["amount"]) / 10**2
                engine.add_job(tokenId, amount)

        engine.compute()

        data = engine.get()
        if data != None:
            return {
                'token_errors': data['errors'],
                'stakers': data["output"],
            }
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to fetch snapshot')

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to snapshot, try again shortly or contact support if error continues.')

def validPenalty(startTime: int):
    currentTime = int(time()*1000)
    timeStaked = currentTime - startTime
    weeksStaked = int(timeStaked/week)
    return 0 if (weeksStaked >= 8) else 5  if (weeksStaked >= 6) else 12.5 if (weeksStaked >= 4) else 20 if (weeksStaked >= 2) else 25
            
@r.post("/staked/", name="staking:staked")
async def staked(req: AddressList):
    CACHE_TTL = 600 # 10 mins
    try:
        stakeKeys = {}
        for address in req.addresses:
            # cache balance confirmed
            ok = False
            data = None
            cached = cache.get(f"get_staking_staked_addresses_{address}_balance_confirmed")
            if cached:
                ok = True
                data = cached
            else:
                res = requests.get(f'{CFG.explorer}/addresses/{address}/balance/confirmed')
                ok = res.ok
                if ok:
                    data = res.json()
                    cache.set(f"get_staking_staked_addresses_{address}_balance_confirmed", data, CACHE_TTL)
            if ok:
                if 'tokens' in data:
                    for token in data["tokens"]:
                        if 'name' in token and 'tokenId' in token:
                            if token["name"] is not None:
                                if "Stake Key" in token["name"]:
                                    stakeKeys[token["tokenId"]] = address
            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failure to fetch balance for {address}')
        
        totalStaked = 0
        stakePerAddress = {}
        
        # getTokenBoxes from cache
        checkBoxes = []
        cached = cache.get(f"get_staking_staked_token_boxes_{CFG.stakeTokenID}")
        if cached:
            checkBoxes = cached
        else:
            checkBoxes = getUnspentStakeBoxes()
            cache.set(f"get_staking_staked_token_boxes_{CFG.stakeTokenID}", checkBoxes, CACHE_TTL)
        for box in checkBoxes:
            if box["assets"][0]["tokenId"]==CFG.stakeTokenID:
                if box["additionalRegisters"]["R5"]["renderedValue"] in stakeKeys.keys():
                    if stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]] not in stakePerAddress:
                        stakePerAddress[stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]]] = {'totalStaked': 0, 'stakeBoxes': []}
                    stakeBoxR4 = eval(box["additionalRegisters"]["R4"]["renderedValue"])
                    cleanedBox = {
                        'boxId': box["boxId"],
                        'stakeKeyId': box["additionalRegisters"]["R5"]["renderedValue"],
                        'stakeAmount': box["assets"][1]["amount"]/10**2,
                        'penaltyPct': validPenalty(stakeBoxR4[1]),
                        'penaltyEndTime': int(stakeBoxR4[1]+8*week)
                    }
                    stakePerAddress[stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]]]["stakeBoxes"].append(cleanedBox)
                    totalStaked += box["assets"][1]["amount"]/10**2
                    stakePerAddress[stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]]]["totalStaked"] += box["assets"][1]["amount"]/10**2

        logging.debug({'totalStaked': totalStaked, 'addresses': stakePerAddress})
        return {
            'totalStaked': totalStaked,
            'addresses': stakePerAddress
        }

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to determine staked value.')

@r.get("/status/", name="staking:status")
def stakingStatus():
    try:
        # check cache
        cached = cache.get(f"get_api_staking_status")
        if cached:
            return cached

        stakeStateBox = getNFTBox(CFG.stakeStateNFT)
        stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])

        totalStaked = stakeStateR4[0]

        apy = 29300000.0*36500/totalStaked

        ret = {
            'Total amount staked': totalStaked/10**2,
            'Staking boxes': stakeStateR4[2],
            'Cycle start': stakeStateR4[3],
            'APY': apy
        }

        # cache and return
        cache.set(f"get_api_staking_status", ret, timeout=300)
        return ret

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to find status, try again shortly or contact support if error continues.')

def compoundTX(appKit: ErgoAppKit, stakeBoxes: List[str],stakeBoxesOutput: List[OutBox],totalReward: int,emissionBox, emissionR4):
    try:
        emissionAssets = {
                        CFG.emissionNFT: 1
                    }
        if totalReward < emissionBox["assets"][1]["amount"]:
            emissionAssets[CFG.stakedTokenID] = emissionBox["assets"][1]["amount"]-totalReward

        emissionOutput = appKit.buildOutBox(
            value=emissionBox["value"],
            tokens=emissionAssets,
            registers=[ErgoAppKit.ergoValue([
                emissionR4[0],
                emissionR4[1],
                emissionR4[2]-len(stakeBoxes),
                emissionR4[3]],ErgoValueT.LongArray)
            ],
            contract=appKit.contractFromAddress(emissionBox["address"]))

        txFee = int(max(CFG.txFee,(0.001+0.0005*len(stakeBoxesOutput))*nergsPerErg))

        inputs = appKit.getBoxesById([emissionBox["boxId"]]+stakeBoxes+list(getBoxesWithUnspentTokens(nErgAmount=txFee,emptyRegisters=True).keys()))

        unsignedTx = appKit.buildUnsignedTransaction(
            inputs=inputs,
            outputs=[emissionOutput]+stakeBoxesOutput,
            fee=txFee,
            sendChangeTo=Address.create(CFG.ergopadWallet).getErgoAddress()
        )

        return unsignedTx

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to compound, try again shortly or contact support if error continues.')

@r.post("/compound/", name="staking:compound")
async def compound(
    req: APIKeyRequest,
    request: Request,
    # current_user=Depends(get_current_active_superuser)
):
    try:
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)
        stakeBoxes = []
        stakeBoxesOutput = []
        totalReward = 0
        compoundTransactions = []
        # emmission box contains current staking info        
        emissionBox = getNFTBox(CFG.emissionNFT)
        emissionR4 = eval(emissionBox["additionalRegisters"]["R4"]["renderedValue"])
        
        # emission box R4[2] contains current remaining stakers
        if emissionR4[2] <= 0: 
            return {'remainingStakers': 0}
        else:
            logging.debug(f'remaining stakers: {emissionR4[2]}')

        # iterate over all staking boxes
        checkBoxes = getUnspentStakeBoxes()
        for box in checkBoxes:
            # make sure token exists, and ??
            if box["assets"][0]["tokenId"] == CFG.stakeTokenID:
                boxR4 = eval(box["additionalRegisters"]["R4"]["renderedValue"])
                if boxR4[0] == emissionR4[1]:

                    # calc rewards and build tx
                    stakeBoxes.append(box["boxId"])
                    stakeReward = int(box["assets"][1]["amount"] * emissionR4[3] / emissionR4[0])
                    totalReward += stakeReward
                    stakeBoxesOutput.append(appKit.buildOutBox(
                        value=box["value"],
                        tokens={
                            CFG.stakeTokenID: 1,
                            CFG.stakedTokenID: box["assets"][1]["amount"] + stakeReward
                        },
                        registers=[
                            ErgoAppKit.ergoValue([boxR4[0]+1,boxR4[1]],ErgoValueT.LongArray),
                            ErgoAppKit.ergoValue(box["additionalRegisters"]["R5"]["renderedValue"],ErgoValueT.ByteArrayFromHex)
                        ],
                        contract=appKit.contractFromAddress(box["address"])
                    ))

            # every <numBoxes>, go ahead and submit tx
            txId = None
            if len(stakeBoxes)>=req.numBoxes:
                retriesLeft = 10
                while retriesLeft > 0:
                    try:
                        unsignedTx = compoundTX(appKit, stakeBoxes, stakeBoxesOutput, totalReward, emissionBox, emissionR4)
                        signedTX = appKit.signTransactionWithNode(unsignedTx)
                        txId = appKit.sendTransaction(signedTX)
                        retriesLeft = 0
                    except Exception as e:
                        utx = unsignedTx or '[NOPE]'
                        retriesLeft -= 1
                        await asyncio.sleep(3)
                if txId is None:
                    return {'status':'error', 'remainingBoxes': emissionR4[2], 'compoundTx': compoundTransactions}
                compoundTransactions.append(txId)
                emissionR4[2]=emissionR4[2]-len(stakeBoxes)
                emissionBox["assets"][1]["amount"] = emissionBox["assets"][1]["amount"]-totalReward
                emissionBox["boxId"] = signedTX.getOutputsToSpend()[0].getId().toString()
                stakeBoxes = []
                stakeBoxesOutput = []
                totalReward = 0

        if len(stakeBoxes) > 0: 
            unsignedTx = compoundTX(appKit, stakeBoxes, stakeBoxesOutput, totalReward, emissionBox, emissionR4)
            signedTX = appKit.signTransactionWithNode(unsignedTx)
            txId = appKit.sendTransaction(signedTX)
            compoundTransactions.append(txId)
            emissionR4[2]=emissionR4[2]-len(stakeBoxes)
            
        return {'status': 'success', 'remainingBoxes': emissionR4[2], 'compoundTx': compoundTransactions}

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to compound, try again shortly or contact support if error continues.')

@r.post("/emit/", name="staking:emit")
async def emit(
    req: APIKeyRequest,
    request: Request,
    # current_user=Depends(get_current_active_superuser)
):
    try:
        stakeStateBox = getNFTBox(CFG.stakeStateNFT)
        stakePoolBox = getNFTBox(CFG.stakePoolNFT)
        emissionBox = getNFTBox(CFG.emissionNFT)

        stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
        stakePoolR4 = eval(stakePoolBox["additionalRegisters"]["R4"]["renderedValue"])
        emissionR4 = eval(emissionBox["additionalRegisters"]["R4"]["renderedValue"])
        if emissionR4[2] > 0:
            return {'remainingStakersToBeCompounded': emissionR4[2]}

        logging.info(stakeStateBox)
        logging.info(stakePoolBox)
        logging.info(emissionBox)

        currentTime = requests.get(f'{CFG.node}/blocks/lastHeaders/1', headers=dict(headers),timeout=2).json()[0]['timestamp']

        if currentTime < stakeStateR4[3]+stakeStateR4[4]:
            logging.info("Too early for emission")
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Too early for a new emission')

        newStakePoolAmount = stakePoolBox["assets"][1]["amount"] - stakePoolR4[0]
        dust = 0
        if len(emissionBox["assets"]) > 1:
            dust = emissionBox["assets"][1]["amount"]
            newStakePoolAmount += dust

        stakeStateOutput = {
            'value': stakeStateBox["value"],
            'address': stakeStateBox["address"],
            'assets': [
                {
                    'tokenId': stakeStateBox["assets"][0]["tokenId"],
                    'amount': stakeStateBox["assets"][0]["amount"]
                },
                {
                    'tokenId': stakeStateBox["assets"][1]["tokenId"],
                    'amount': stakeStateBox["assets"][1]["amount"]
                },
                ],
            'registers': {
                'R4': encodeLongArray([
                    stakeStateR4[0]+stakePoolR4[0]-dust,
                    stakeStateR4[1]+1,
                    stakeStateR4[2],
                    stakeStateR4[3]+stakeStateR4[4],
                    stakeStateR4[4]
                ])
            }
        }
        
        stakePoolOutput = {
            'value': stakePoolBox["value"],
            'address': stakePoolBox["address"],
            'registers': {'R4': stakePoolBox["additionalRegisters"]["R4"]["serializedValue"]},
            'assets': [
                {
                    'tokenId': stakePoolBox["assets"][0]["tokenId"],
                    'amount': stakePoolBox["assets"][0]["amount"]
                },
                {
                    'tokenId': stakePoolBox["assets"][1]["tokenId"],
                    'amount': newStakePoolAmount
                }
            ]
        }

        emissionOutput = {
            'value': emissionBox["value"],
            'address': emissionBox["address"],
            'assets': [
                {
                    'tokenId': emissionBox["assets"][0]["tokenId"],
                    'amount': emissionBox["assets"][0]["amount"]
                },
                {
                    'tokenId': stakePoolBox["assets"][1]["tokenId"],
                    'amount': stakePoolR4[0]
                }
            ],
            'registers': {
                'R4': encodeLongArray([
                    stakeStateR4[0],
                    stakeStateR4[1],
                    stakeStateR4[2],
                    stakePoolR4[0]
                ])
            }
        }

        inBoxesRaw = []
        for box in [stakeStateBox["boxId"],stakePoolBox["boxId"],emissionBox["boxId"]]+list(getBoxesWithUnspentTokens(nErgAmount=int(0.001*nergsPerErg),emptyRegisters=True).keys()):
            res = requests.get(f'{CFG.node}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
            if res.ok:
                inBoxesRaw.append(res.json()['bytes'])
            else:
                return res

        tx = {
            'requests': [stakeStateOutput,stakePoolOutput,emissionOutput],
            'fee': int(0.001*nergsPerErg),
            'inputsRaw': inBoxesRaw
        }
        logging.info(tx)

        res = requests.post(f'{CFG.node}/wallet/transaction/send', headers=dict(headers, **{'api_key': req.apiKey}), json=tx)  
        logging.info(res.content) 

        return {
            'stakers': stakeStateR4[2],
            'amountStaked': stakeStateR4[0],
            'nextEmissionTime': stakeStateR4[3]+stakeStateR4[4],
            'dustPreviousEmission': dust,
            'emissionTx': res.json()
        }

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to emit, try again shortly or contact support if error continues.')

@r.post("/stake/", name="staking:stake")
async def stake(req: StakeRequest):
    try:
        logging.debug(f'stake::staked token info')
        stakedTokenInfo = getTokenInfo(CFG.stakedTokenID)

        logging.debug(f'stake::appkit')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)

        logging.debug(f'stake::stakeAppkit.es')
        with open(f'contracts/stakeAppkit.es') as f:
            script = f.read()
        stakeTree = appKit.compileErgoScript(
            script,
            {
                "_stakeStateNFT": ErgoAppKit.ergoValue(CFG.stakeStateNFT, ErgoValueT.ByteArrayFromHex).getValue(),
                "_emissionNFT": ErgoAppKit.ergoValue(CFG.emissionNFT, ErgoValueT.ByteArrayFromHex).getValue()    
            }
        )

        logging.debug(f'stake::get NFT box')
        stakeStateBox = getNFTBox(CFG.stakeStateNFT)

        logging.debug(f'stake::token amount')
        tokenAmount = int(req.amount*10**stakedTokenInfo["decimals"])
        
        logging.debug(f'stake::r4')
        r4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
        stakeStateOutput = appKit.buildOutBox(
            value=stakeStateBox["value"],
            tokens={
                stakeStateBox["assets"][0]["tokenId"]: stakeStateBox["assets"][0]["amount"],
                stakeStateBox["assets"][1]["tokenId"]: stakeStateBox["assets"][1]["amount"]-1
            },
            registers=[ErgoAppKit.ergoValue([int(r4[0])+tokenAmount,
                        int(r4[1]),
                        int(r4[2])+1,
                        int(r4[3]),
                        int(r4[4])], ErgoValueT.LongArray)],
            contract=appKit.contractFromAddress(stakeStateBox["address"])
        )

        logging.debug(f'stake::build outbox stakeOutput')
        stakeOutput = appKit.buildOutBox(
            value=int(0.001*nergsPerErg),
            tokens={
                stakeStateBox["assets"][1]["tokenId"]: 1,
                CFG.stakedTokenID: tokenAmount
            },
            registers=[
                ErgoAppKit.ergoValue([
                    int(r4[1]),
                    int(time()*1000)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(stakeStateBox["boxId"],ErgoValueT.ByteArrayFromHex)
            ],
            contract=appKit.contractFromTree(stakeTree)
        )
        userInputs = List[InputBox]
        tokensToSpend = {CFG.stakedTokenID: tokenAmount}

        try: logging.debug(f'stake::count utxos=={req.utxos}')
        except: pass
        if len(req.utxos) == 0:
            if len(req.addresses) == 0:
                userInputs = appKit.boxesToSpend(req.wallet,int(28e7),tokensToSpend)
            else:
                userInputs = appKit.boxesToSpendFromList(req.addresses,int(28e7),tokensToSpend)
        else:
            userInputs = appKit.getBoxesById(req.utxos)
            if not ErgoAppKit.boxesCovered(userInputs,int(28e7),tokensToSpend):
                userInputs = appKit.boxesToSpend(req.wallet,int(28e7),tokensToSpend)
        if userInputs is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Could not find enough erg and/or tokens')

        logging.debug('stake::mint token')
        userOutput = appKit.mintToken(
            value=int(0.01*nergsPerErg),
            tokenId=stakeStateBox["boxId"],
            tokenName=f'{stakedTokenInfo["name"]} Stake Key',
            tokenDesc=f'{{"originalAmountStaked": {req.amount}, "stakeTime": "{datetime.now()}"}}',
            mintAmount=1,
            decimals=0,
            contract=appKit.contractFromTree(userInputs[0].getErgoTree())
        )
        
        logging.debug('stake::build outbox for fee')
        feeOutput = appKit.buildOutBox(
            value=int(0.25*nergsPerErg),
            tokens=None,
            registers=None,
            contract=appKit.contractFromAddress(CFG.ergopadWallet)
        )

        logging.debug('stake::inputs/outputs')
        inputs = appKit.getBoxesById([stakeStateBox["boxId"]])+userInputs
        outputs = [stakeStateOutput,stakeOutput,userOutput,feeOutput]

        logging.debug('stake::build utx')
        unsignedTx = appKit.buildUnsignedTransaction(
            inputs=inputs,
            outputs=outputs,
            fee=int(0.001*nergsPerErg),
            sendChangeTo=Address.create(req.wallet).getErgoAddress()
        )

        logging.debug(f'stake::txFormat=={req.txFormat}')
        if req.txFormat == TXFormat.EIP_12:
            logging.debug('stake::utx to json')
            return ErgoAppKit.unsignedTxToJson(unsignedTx)
                
        if req.txFormat == TXFormat.ERGO_PAY:
            logging.debug('stake::reduced tx')
            reducedTx = appKit.reducedTx(unsignedTx)
            ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                reducedTx,
                address=req.wallet
            )
            cache.set(f'ergopay_signing_request_{unsignedTx.getId()}',ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{unsignedTx.getId()}'}

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to stake, try again shortly or contact support if error continues.')

# bootstrap staking setup
@r.post("/bootstrap/", name="staking:bootstrap")
async def bootstrapStaking(req: BootstrapRequest):
    try:
        stakedToken = getTokenInfo(req.stakedTokenID)
        stakedTokenDecimalMultiplier = 10**stakedToken["decimals"]
        
        stakeStateNFT = getTokenInfo(req.stakeStateNFT)
        if (stakeStateNFT["name"] != f'{stakedToken["name"]} Stake State'):
            return({"success": False, "Error": f"Wrong name for stake state NFT {stakeStateNFT['name']}"})
        if (stakeStateNFT["emissionAmount"]>1):
            return({"success": False, "Error": f"There should only be one {stakeStateNFT['name']}"})

        stakePoolNFT = getTokenInfo(req.stakePoolNFT)
        if (stakePoolNFT["name"] != f'{stakedToken["name"]} Stake Pool'):
            return({"success": False, "Error": f"Wrong name for stake pool NFT {stakePoolNFT['name']}"})
        if (stakePoolNFT["emissionAmount"]>1):
            return({"success": False, "Error": f"There should only be one {stakePoolNFT['name']}"})

        emissionNFT = getTokenInfo(req.emissionNFT)
        if (emissionNFT["name"] != f'{stakedToken["name"]} Emission'):
            return({"success": False, "Error": f"Wrong name for emission NFT {emissionNFT['name']}"})
        if (emissionNFT["emissionAmount"]>1):
            return({"success": False, "Error": f"There should only be one {emissionNFT['name']}"})

        stakeTokenID = getTokenInfo(req.stakeTokenID)
        if (stakeTokenID["name"] != f'{stakedToken["name"]} Stake Token'):
            return({"success": False, "Error": f"Wrong name for stake token {stakeTokenID['name']}"})
        if (stakeTokenID["emissionAmount"]<1000000000):
            return({"success": False, "Error": f"There should only be at least a billion {stakeTokenID['name']}"})

        params = {}
        params["stakedTokenID"] = hexstringToB64(req.stakedTokenID)
        params["stakePoolNFT"] = hexstringToB64(req.stakePoolNFT)
        params["emissionNFT"] = hexstringToB64(req.emissionNFT)
        params["stakeStateNFT"] = hexstringToB64(req.stakeStateNFT)
        params["stakeTokenID"] = hexstringToB64(req.stakeTokenID)
        params["timestamp"] = int(time())

        emissionAddress = getErgoscript("emission",params=params)
        stakePoolAddress = getErgoscript("stakePool", params=params)
        stakeAddress = getErgoscript("stake",params=params)
        stakeWallet = Wallet(stakeAddress)
        stakeErgoTreeBytes = bytes.fromhex(stakeWallet.ergoTree()[2:])
        stakeHash = b64encode(blake2b(stakeErgoTreeBytes, digest_size=32).digest()).decode('utf-8')

        params["stakeContractHash"] = stakeHash

        stakeStateAddress = getErgoscript("stakeState",params=params)
        stakePoolBox = {
            'address': stakePoolAddress,
            'value': int(0.001*nergsPerErg),
            'registers': {
                'R4': encodeLongArray([int(req.emissionAmount*stakedTokenDecimalMultiplier)])
            },
            'assets': [
                {
                    'tokenId': req.stakePoolNFT,
                    'amount': 1
                },
                {
                    'tokenId': req.stakedTokenID,
                    'amount': req.stakeAmount*stakedTokenDecimalMultiplier
                }
            ]
        }

        stakeStateBox = {
            'address': stakeStateAddress,
            'value': int(0.001*nergsPerErg),
            'registers': {
                'R4': encodeLongArray([0,0,0,int(time()*1000),req.cycleDuration_ms])
            },
            'assets': [
                {
                    'tokenId': req.stakeStateNFT,
                    'amount': 1
                },
                {
                    'tokenId': req.stakeTokenID,
                    'amount': 1000000000
                }
            ]
        }

        emissionBox = {
            'address': emissionAddress,
            'value': int(0.001*nergsPerErg),
            'registers': {
                'R4': encodeLongArray([0,-1,0,req.emissionAmount*stakedTokenDecimalMultiplier])
            },
            'assets': [
                {
                    'tokenId': req.emissionNFT,
                    'amount': 1
                }
            ]
        }

        res = {
            'requests': [stakeStateBox,emissionBox,stakePoolBox],
            'fee': int(0.001*nergsPerErg)
        }
        return(res)

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to bootstrap, try again shortly or contact support if error continues.')

@r.post("/{project}/stake/", name="staking:stake-v2")
async def stakeV2(project: str, req: StakeRequest):
    try:
        if project not in stakingConfigs:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{project} does not have a staking config')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)
        config = stakingConfigs[project](appKit)
        tokenAmount = round(req.amount*10**config.stakedTokenDecimals)
        assetsRequired = CreateStakeProxyTransaction.assetsRequired(config,tokenAmount)
        userInputs = appKit.boxesToSpendFromList(req.addresses,assetsRequired.nErgRequired,assetsRequired.tokensRequired)
        stakeProxyTx = CreateStakeProxyTransaction(userInputs,config,tokenAmount,req.wallet)

        if req.txFormat == TXFormat.EIP_12:
            return stakeProxyTx.eip12
            
        if req.txFormat == TXFormat.ERGO_PAY:
            cache.set(f'ergopay_signing_request_{stakeProxyTx.unsignedTx.getId()}',stakeProxyTx.ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{stakeProxyTx.unsignedTx.getId()}'}

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to stake, please make sure you have at least 0.5 erg in wallet.')

@r.post("/{project}/unstake/", name="staking:unstake-v2")
async def unstakev2(project: str, req: UnstakeRequest):
    try:
        if project not in stakingConfigs:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{project} does not have a staking config')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)
        config = stakingConfigs[project](appKit)
        stakeInput = appKit.getBoxesById([req.stakeBox])[0]
        tokenAmount = round(req.amount*10**config.stakedTokenDecimals)
        remaining = stakeInput.getTokens()[0].getValue() - tokenAmount
        if remaining > 0 and remaining < 1000:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'A partial unstake needs to leave at least {remaining/10**config.stakedTokenDecimals} tokens remaining')
        assetsRequired = CreateUnstakeProxyTransaction.assetsRequired(config,tokenAmount,stakeInput)
        userInputs = appKit.boxesToSpendFromList(req.addresses,assetsRequired.nErgRequired,assetsRequired.tokensRequired)
        unstakeProxyTx = CreateUnstakeProxyTransaction(userInputs,stakeInput,config,req.amount*10**config.stakedTokenDecimals,req.address)

        if req.txFormat == TXFormat.EIP_12:
            return unstakeProxyTx.eip12
            
        if req.txFormat == TXFormat.ERGO_PAY:
            cache.set(f'ergopay_signing_request_{unstakeProxyTx.unsignedTx.getId()}',unstakeProxyTx.ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{unstakeProxyTx.unsignedTx.getId()}'}

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to unstake, please make sure you have at least 0.5 erg in wallet.')

@r.post("/{project}/addstake/", name="staking:addstake-v2")
async def addstake(project: str, req: UnstakeRequest):
    try:
        if project not in stakingConfigs:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{project} does not have a staking config')
        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)
        config = stakingConfigs[project](appKit)
        stakeInput = appKit.getBoxesById([req.stakeBox])[0]
        tokenAmount = round(req.amount*10**config.stakedTokenDecimals)
        assetsRequired = CreateAddStakeProxyTransaction.assetsRequired(config,tokenAmount,stakeInput)
        userInputs = appKit.boxesToSpendFromList(req.addresses,assetsRequired.nErgRequired,assetsRequired.tokensRequired)
        addStakeProxyTx = CreateAddStakeProxyTransaction(userInputs,stakeInput,config,tokenAmount,req.address)

        if req.txFormat == TXFormat.EIP_12:
            return addStakeProxyTx.eip12
            
        if req.txFormat == TXFormat.ERGO_PAY:
            cache.set(f'ergopay_signing_request_{addStakeProxyTx.unsignedTx.getId()}',addStakeProxyTx.ergoPaySigningRequest)
            return {'url': f'ergopay://ergopad.io/api/blockchain/signingRequest/{addStakeProxyTx.unsignedTx.getId()}'}

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to add stake, please make sure you have at least 0.5 erg in wallet.')

@r.get("/{project}/status/", name="staking:status-v2")
def stakingStatus(project: str):
    try:
        if project not in stakingConfigs:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{project} does not have a staking config')
        # check cache
        cached = cache.get(f"get_api_staking_status_{project}")
        if cached:
            return cached

        appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)
        config = stakingConfigs[project](appKit)

        stakeStateBox = getNFTBox(config.stakeStateNFT)
        stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
        stakePoolBox = getNFTBox(config.stakePoolNFT)
        stakePoolR4 = eval(stakePoolBox["additionalRegisters"]["R4"]["renderedValue"])

        totalStaked = stakeStateR4[0]
        cycleEmission = stakePoolR4[0]
        dailyEmission = cycleEmission*86400000/stakeStateR4[4]

        apy = round(dailyEmission*36500/totalStaked,2)

        ret = {
            'Total amount staked': totalStaked/10**config.stakedTokenDecimals,
            'Staking boxes': stakeStateR4[2],
            'Cycle start': stakeStateR4[3],
            'APY': apy
        }

        # cache and return
        cache.set(f"get_api_staking_status_{project}", ret, timeout=300)
        return ret

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to find status, try again shortly or contact support if error continues.')

@r.post("/{project}/staked/", name="staking:staked-v2")
async def stakedv2(project: str, req: AddressList):
    if project not in stakingConfigs:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{project} does not have a staking config')

    CACHE_TTL = 600 # 10 mins
    appKit = ErgoAppKit(CFG.node,Network,CFG.explorer)
    config = stakingConfigs[project](appKit)
    try:
        stakeKeys = {}
        for address in req.addresses:
            # cache balance confirmed
            ok = False
            data = None
            cached = cache.get(f"get_staking_staked_addresses_{address}_balance_confirmed")
            if cached:
                ok = True
                data = cached
            else:
                res = requests.get(f'{CFG.explorer}/addresses/{address}/balance/confirmed')
                ok = res.ok
                if ok:
                    data = res.json()
                    cache.set(f"get_staking_staked_addresses_{address}_balance_confirmed", data, CACHE_TTL)
            if ok:
                if 'tokens' in data:
                    for token in data["tokens"]:
                        if 'name' in token and 'tokenId' in token:
                            if token["name"] is not None:
                                if "Stake Key" in token["name"]:
                                    stakeKeys[token["tokenId"]] = address
            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Failure to fetch balance for {address}')
        
        totalStaked = 0
        stakePerAddress = {}
        
        # getTokenBoxes from cache
        checkBoxes = []
        cached = cache.get(f"get_staking_staked_token_boxes_{config.stakeTokenId}")
        if cached:
            checkBoxes = cached
        else:
            checkBoxes = getUnspentStakeBoxes(config.stakeTokenId,config.stakeContract.contract.toAddress().toString(),True)
            cache.set(f"get_staking_staked_token_boxes_{config.stakeTokenId}", checkBoxes, CACHE_TTL)
        for box in checkBoxes:
            if box["assets"][0]["tokenId"]==config.stakeTokenId:
                if box["additionalRegisters"]["R5"]["renderedValue"] in stakeKeys.keys():
                    if stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]] not in stakePerAddress:
                        stakePerAddress[stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]]] = {'totalStaked': 0, 'stakeBoxes': []}
                    stakeBoxR4 = eval(box["additionalRegisters"]["R4"]["renderedValue"])
                    cleanedBox = {
                        'boxId': box["boxId"],
                        'stakeKeyId': box["additionalRegisters"]["R5"]["renderedValue"],
                        'stakeAmount': round(box["assets"][1]["amount"]/10**config.stakedTokenDecimals,config.stakedTokenDecimals)
                    }
                    stakePerAddress[stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]]]["stakeBoxes"].append(cleanedBox)
                    totalStaked += round(box["assets"][1]["amount"]/10**config.stakedTokenDecimals,config.stakedTokenDecimals)
                    stakePerAddress[stakeKeys[box["additionalRegisters"]["R5"]["renderedValue"]]]["totalStaked"] += round(box["assets"][1]["amount"]/10**config.stakedTokenDecimals,config.stakedTokenDecimals)

        return {
            'project': project,
            'tokenName': config.stakedTokenName,
            'totalStaked': totalStaked,
            'addresses': stakePerAddress
        }

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to determine staked value.')

@r.post("/staked-v2/", name="staking:all-staked-v2")
async def allstakedv2(req: AddressList):
    try:
        # creating a hash for the input that is independent of ordering
        u_hash = "hash_" + str(sum(list(map(lambda address: int(get_md5_hash(address), 16), set(req.addresses)))))
        cached = cache.get(f"get_staking_staked_v2_{u_hash}")
        if cached:
            logging.info(f"INFO:{myself()}: cache hit")
            return cached

        ret = []
        for project in stakingConfigs:
            staked = await stakedv2(project, req)
            if type(staked) == JSONResponse:
                # error
                return staked
            if staked["totalStaked"] == 0:
                # filter 0 values
                continue
            ret.append(staked)

        cache.set(f"get_staking_staked_v2_{u_hash}", ret)
        return ret

    except Exception as e:
        logging.error(f'ERR:{myself()}: ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: Unable to determine staked value.')

########################################
########## STAKING CONFIG CMS ##########
########################################

@r.get("/config", response_model_exclude_none=True, name="staking-cms:all-config")
async def staking_config_list_cms(
    db=Depends(get_db),
):
    """
    Get all config
    """
    try:
        return get_all_staking_config(db)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get("/config/{project}", response_model_exclude_none=True, name="staking-cms:config")
async def staking_config_cms(
    project: str,
    db=Depends(get_db),
):
    """
    Get config
    """
    try:
        return get_staking_config_by_name(db, project)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post("/config", response_model_exclude_none=True, name="staking-cms:create-config")
async def staking_config_create_cms(
    staking_config: CreateAndUpdateStakingConfig,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new staking config
    """
    try:
        return create_staking_config(db, staking_config)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.put("/config/{id}", response_model_exclude_none=True, name="staking-cms:edit-config")
async def staking_config_edit_cms(
    id: int,
    staking_config: CreateAndUpdateStakingConfig,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing config
    """
    try:
        return edit_staking_config(db, id, staking_config)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.delete(
    "/config/{id}", response_model_exclude_none=True, name="staking-cms:edit-config"
)
async def staking_config_delete_cms(
    id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Delete config
    """
    try:
        return delete_staking_config(db, id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )
