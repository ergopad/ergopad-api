from enum import Enum
import requests, json
from wallet import Wallet

from starlette.responses import JSONResponse
from fastapi import APIRouter, status
from time import time
from api.v1.routes.asset import get_asset_current_price
from config import Config, Network # api specific config

CFG = Config[Network]

blockchain_router = r = APIRouter()

#region BLOCKHEADER
"""
Blockchain API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: allow purchase/redeem tokens locked by ergopad scripts
Contributor(s): https://github.com/Luivatra

Notes:
- /utils/ergoTreeToAddress/{ergoTreeHex} can convert from ergotree (in R4)

** PREPARE FOR PROD
!! figure out proper payment amounts to send !!

Later
- build route that tells someone how much they have locked
?? log to database?
.. common events
.. purchase/token data
- add route to show value assigned to wallet?
- build route that tells someone how much they have locked
- set vestingBegin_ms to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)

Complete
- restart with PROD; move CFG back to docker .env
.. verify wallet address
- disable /payment route (only for testing)
.. set debug flag?
- log to database?
.. common events
.. purchase/token data
- add route to show value assigned to wallet?
- /utils/ergoTreeToAddress/{ergoTreeHex} can convert from ergotree (in R4)
- push changes
.. remove keys
.. merge to main
- set vestingBegin_ms to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)
"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug

try:
    headers            = {'Content-Type': 'application/json'}
    tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')
    nodeWallet         = Wallet('9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285') # contains ergopad tokens (xerg10M)
    buyerWallet        = Wallet('9iLSsvi2zobapQmi7tXVK4mnrbQwpK3oTfPcCpF9n7J2DQVpxq2') # simulate buyer / seed tokens

except Exception as e:
    logging.error(f'Init {e}')
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

class TXFormat(str, Enum):
    EIP_12 = "eip-12"
    NODE = "node"
    ERGO_PAY = "ergo_pay"

#region ROUTES
# current node info (and more)
@r.get("/info", name="blockchain:info")
async def getInfo():
    try:
        st = time() # stopwatch
        nodeInfo = {}

        # ergonode
        res = requests.get(f'{CFG.node}/info', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), timeout=2)
        if res.ok:
            i = res.json()
            # nodeInfo['network'] = Network
            # nodeInfo['uri'] = CFG.node
            nodeInfo['ergonodeStatus'] = 'ok'
            if 'headersHeight' in i: nodeInfo['currentHeight'] = i['headersHeight']
            if 'currentTime' in i: nodeInfo['currentTime_ms'] = i['currentTime']
        else:
            nodeInfo['ergonode'] = 'error'

        # assembler
        res = requests.get(f'{CFG.assembler}/state', headers=headers, timeout=2)
        if res.ok:
            nodeInfo['assemblerIsFunctioning'] = res.json()['functioning']
            nodeInfo['assemblerStatus'] = 'ok'
        else:
            nodeInfo['assemblerIsFunctioning'] = 'invalid'
            nodeInfo['assemblerStatus'] = 'error'

        # wallet and token
        # CAREFULL!!! XXX nodeInfo['apikey'] = CFG.ergopadApiKey XXX
        nodeInfo['network'] = Network
        nodeInfo['ergopadTokenId'] = CFG.ergopadTokenId
        if DEBUG:
            nodeInfo['buyer'] = buyerWallet.address
        nodeInfo['seller'] = nodeWallet.address

        # nodeInfo['vestingBegin_ms'] = f'{ctime(1643245200)} UTC'
        nodeInfo['sigUSD'] = await get_asset_current_price('sigusd')
        nodeInfo['inDebugMode'] = ('PROD', '!! DEBUG !!')[DEBUG]

        logging.debug(f'::TOOK {time()-st:0.4f}s')
        return nodeInfo

    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid blockchain info ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid blockchain info')

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
    # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
    try:
        tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
        return tkn.json()
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid token request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid token request')

@r.get("/boxInfo/{boxId}", name="blockchain:boxInfo")
def getBoxInfo(boxId):
    try:
        box = requests.get(f'{CFG.explorer}/boxes/{boxId}')
        return box.json()
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid box request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid token request')

@r.get("/transactionInfo/{transactionId}", name="blockchain:transactionInfo")
def getTransactionInfo(transactionId):
    try:
        tx = requests.get(f'{CFG.explorer}/transactions/{transactionId}')
        return tx.json()
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid box request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid token request')

# special request for CMC
@r.get("/emissionAmount/{tokenId}", name="blockchain:emissionAmount")
def getEmmissionAmount(tokenId):
    try:
        tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
        decimals = tkn.json()['decimals']
        emissionAmount = tkn.json()['emissionAmount'] / 10**decimals
        return emissionAmount
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid token request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid token request')

# assember follow info
@r.get("/followInfo/{followId}", name="blockchain:followInfo")
def followInfo(followId):
    try:
        res = requests.get(f'{CFG.assembler}/result/{followId}')
        return res.json()

    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid assembly follow ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid assembly follow')

def getInputBoxes(boxes, txFormat: TXFormat):
    if txFormat==TXFormat.NODE:
        inBoxesRaw = []
        for box in boxes:
            res = requests.get(f'{CFG.node}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
            if res.ok:
                inBoxesRaw.append(res.json()['bytes'])
            else:
                return res
        return inBoxesRaw
    if txFormat==TXFormat.EIP_12:
        unsignedInputs = []
        for ibox in boxes:
            res = requests.get(f'{CFG.node}/utxo/withPool/byId/{ibox}', headers=dict(headers), timeout=2)
            if res.ok:
                box = res.json()
                unsignedInputs.append({
                    'extension': {},
                    'boxId': box["boxId"],
                    'value': str(box["value"]),
                    'ergoTree': box["ergoTree"],
                    'assets': json.loads(json.dumps(box["assets"]), parse_int=str),
                    'additionalRegisters': box["additionalRegisters"],
                    'creationHeight': box["creationHeight"],
                    'transactionId': box["transactionId"],
                    'index': box["index"]
                })
        return unsignedInputs
    return None

def getNFTBox(tokenId: str):
    try:
        memRes = requests.get(f'{CFG.explorer}/mempool/boxes/unspent')
        if memRes.ok:
            memResJson = []
            memResContent = memRes.content.decode('utf-8')
            index = 0
            offset = 0
            while index < len(memResContent):
                index += 1
                try:
                    newElement = json.loads(memResContent[offset:index])
                    memResJson.append(newElement)
                    offset = index
                except:
                    pass
            for memBox in memResJson:
                logging.info(memBox)
                if "assets" in memBox:
                    for token in memBox["assets"]:
                        if token["tokenId"]==tokenId:
                            return memBox
        res = requests.get(f'{CFG.explorer}/boxes/unspent/byTokenId/{tokenId}')
        if res.ok:
            items = res.json()["items"]
            if len(items) == 1:
                return items[0]
            else:
                logging.error(f'ERR:{myself()}: multiple nft box ({e})')
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find nft box ({e})')
        return None

def getTokenBoxes(tokenId: str, offset: int = 0, limit: int = 100):
    try:
        res = requests.get(f'{CFG.explorer}/boxes/unspent/byTokenId/{tokenId}?offset={offset}&limit={limit}')
        if res.ok:
            items = res.json()["items"]
            return items
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find token box ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to find token box')

# find unspent boxes with tokens
@r.get("/unspentTokens", name="blockchain:unspentTokens")
def getBoxesWithUnspentTokens(nErgAmount=-1, tokenId=CFG.ergopadTokenId, tokenAmount=-1, allowMempool=True, emptyRegisters=False):
    try:
        foundTokenAmount = 0
        foundNErgAmount = 0
        ergopadTokenBoxes = {}

        res = requests.get(f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}))
        if res.ok:
            assets = res.json()
            for ast in assets:
                if 'box' in ast:
                    if not emptyRegisters or len(ast['box']['additionalRegisters']) == 0:
                        # find enough boxes to handle nergs requested
                        if foundNErgAmount < nErgAmount:
                            foundNErgAmount += ast['box']['value']
                            ergopadTokenBoxes[ast['box']['boxId']] = []

                        # find enough boxes with tokens to handle request
                        if ast['box']['assets'] != [] and (foundTokenAmount < tokenAmount or tokenAmount == -1):
                            for tkn in ast['box']['assets']:
                                if 'tokenId' in tkn and 'amount' in tkn:
                                    #logging.info(tokenId)
                                    if tkn['tokenId'] == tokenId:
                                        foundTokenAmount += tkn['amount']
                                        if ast['box']['boxId'] in ergopadTokenBoxes:
                                            ergopadTokenBoxes[ast['box']['boxId']].append(tkn)
                                        else:
                                            ergopadTokenBoxes[ast['box']['boxId']] = [tkn]
                                            foundNErgAmount += ast['box']['value']
                                        # logging.debug(tkn)

            logging.info(f'found {foundTokenAmount} ergopad tokens and {foundNErgAmount} nErg in wallet')

        # invalid wallet, no unspent boxes, etc..
        else:
            logging.error('unable to find unspent boxes')

        # return CFG.node
        # return f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}, apikey={CFG.ergopadApiKey}'
        return ergopadTokenBoxes

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find unspent tokens ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to find unspent tokens')

# ergoscripts
@r.get("/script/{name}", name="blockchain:getErgoscript")
def getErgoscript(name, params={}):
    try:
        script = None
        if name == 'alwaysTrue':
            script = f"""{{
                val x = 1
                val y = 1

                sigmaProp( x == y )
            }}"""

        if name == 'neverTrue':
            script = "{ 1 == 0 }"

        # params = {'buyerWallet': '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG'}
        if name == 'ergopad':
            script = f"""{{
                val buyer = PK("{params['buyerWallet']}").propBytes
                val seller = PK("{params['nodeWallet']}").propBytes // ergopad.io
                val isValid = {{
                        //
                        val voucher = OUTPUTS(0).R4[Long].getOrElse(0L)

                        // voucher == voucher // && // TODO: match token
                        buyer == INPUTS(0).propositionBytes
                }}

                sigmaProp(1==1)
            }}"""


        if script is None:
            with open(f'contracts/{name}.es') as f:
                unformattedScript = f.read()
            script = unformattedScript.format(**params)
        request = {'source': script}

        logging.debug(f'Script: {script}')
        # get the P2S address (basically a hash of the script??)
        p2s = requests.post(f'{CFG.node}/script/p2sAddress', headers=headers, json=request)
        logging.debug(f'p2s: {p2s.content}')
        smartContract = p2s.json()['address']
        # logging.debug(f'smart contract: {smartContract}')
        # logging.info(f':::{name}:::{script}')

        return smartContract

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to build script ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to build script')

#endregion ROUTES

### MAIN
if __name__ == '__main__':
        print('API routes: ...')