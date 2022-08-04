from configparser import SafeConfigParser
from decimal import Decimal
from enum import Enum
from typing import Dict
from xmlrpc.client import Boolean
import requests, json
from core.auth import get_current_active_superuser
from db.session import engDanaides
from ergo_python_appkit.appkit import ErgoAppKit
from wallet import Wallet

from sqlalchemy import create_engine, text
from starlette.responses import JSONResponse
from fastapi import APIRouter, Depends, status
from time import time
from api.v1.routes.asset import get_asset_balance_from_address, get_asset_current_price
from cache.cache import cache
from config import Config, Network # api specific config
from pydantic import BaseModel
from cache.cache import cache

CFG = Config[Network]
DEBUG = CFG.debug

blockchain_router = r = APIRouter()

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region INIT
DATABASE = CFG.connectionString
EXPLORER = CFG.csExplorer
STAKE_ADDRESS = '3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9'
STAKE_KEY_ID = '1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee'

try:
    headers            = {'Content-Type': 'application/json'}
    tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')

except Exception as e:
    logging.error(f'Init {e}')
#endregion INIT

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

        # wallet and token
        # CAREFULL!!! XXX nodeInfo['apikey'] = CFG.ergopadApiKey XXX
        nodeInfo['network'] = Network
        nodeInfo['ergopadTokenId'] = CFG.ergopadTokenId
        nodeInfo['inDebugMode'] = ('PROD', '!! DEBUG !!')[DEBUG]

        logging.debug(f'::TOOK {time()-st:0.4f}s')
        return nodeInfo

    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid blockchain info ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid blockchain info ({e})')

@r.get("/tokenomics/{tokenId}", name="blockchain:tokenomics")
async def tokenomics(tokenId):
    try:
        sqlTokenomics = text(f'''
            select token_name
                , token_id
                , token_price
                , current_total_supply/power(10, decimals) as current_total_supply
                , emission_amount/power(10, decimals) as initial_total_supply
                , (emission_amount - current_total_supply)/power(10, decimals) as burned
                , token_price * (current_total_supply - vested - emitted - coalesce(tokens.stake_pool, 0))/power(10, decimals) as market_cap
                , (current_total_supply - vested - emitted - coalesce(tokens.stake_pool, 0))/power(10, decimals) as in_circulation
            from tokens
            where token_id = :token_id
        ''')
        with engDanaides.begin() as con:
            res = con.execute(sqlTokenomics, {'token_id': tokenId}).fetchone()

        stats = {
            'token_id': res['token_id'],
            'token_name': res['token_name'],
            'token_price': res['token_price'],
            'current_total_supply': res['current_total_supply'],
            'initial_total_supply': res['initial_total_supply'],
            'burned': res['burned'],
            'market_cap': res['market_cap'],
            'in_circulation': res['in_circulation'],
        }

        return stats

    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid tokenomics request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid tokenomics request ({e})')

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
    # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
    try:
        sqlTokenomics = text(f'''
            select token_name
                , token_id
                , token_price
                , decimals
                , coalesce(amount, 0.0) as emission_amount
            from tokens
            where token_id = :token_id
        ''')
        with engDanaides.begin() as con:
            res = con.execute(sqlTokenomics, {'token_id': tokenId}).fetchone()

        return {
            'id': res['token_id'],
            'boxId': '',
            'emissionAmount': res['emission_amount'],
            'name': res['token_name'],
            'description': '',
            'type': '',
            'decimals': res['decimals'],
            # 'price': res['token_price'],
        }
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid token request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid token request ({e})')


@r.get("/boxInfo/{boxId}", name="blockchain:boxInfo")
def getBoxInfo(boxId):
    try:
        box = requests.get(f'{CFG.explorer}/boxes/{boxId}')
        return box.json()
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid box request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid box request ({e})')


@r.get("/transactionInfo/{transactionId}", name="blockchain:transactionInfo")
def getTransactionInfo(transactionId):
    try:
        tx = requests.get(f'{CFG.explorer}/transactions/{transactionId}')
        return tx.json()
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid tx info ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid tx info ({e})')


# request by CMC
@r.get("/emissionAmount/{token_id}", name="blockchain:emissionAmount")
def getEmmissionAmount(token_id):
    try:
        sql = text(f'''
            select emission_amount/power(10, decimals)
            from tokens
            where token_id = :token_id
        ''')
        with engDanaides.begin() as con:
            res = con.execute(sql, {'token_id': token_id}).fetchone()

        return res['emission_amount']
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid getEmmissionAmount request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid getEmmissionAmount request ({e})')


@r.get("/ergusdoracle", name="blockchain:ergusdoracle")
async def ergusdoracle():
    res = requests.get("https://erg-oracle-ergusd.spirepools.com/frontendData")
    return json.loads(res.json())


# find value from token and address
def sqlTokenValue(address, token_id, con):
    try:
        sql = text(f'''
            select a.amount/power(10, t.decimals) as res 
				--, a.token_id, t.token_name
			from assets a
				left join tokens t on t.token_id = a.token_id
			where address = :address
				and a.token_id = :token_id
        ''')
        res = con.execute(sql).fetchone()

        return res['res']
    except:
        return 0


# paideia tokenId: 1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489
@r.get("/paideiaInCirculation", name="blockchain:paideiaInCirculation")
async def paideiaInCirculation():
    try:
        token_id = '1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489'
        sql = text(f'''
            select token_name
                , token_id
                , token_price
                , current_total_supply/power(10, decimals) as current_total_supply
                , emission_amount/power(10, decimals) as initial_total_supply
                , (emission_amount - current_total_supply)/power(10, decimals) as burned
                , token_price * (current_total_supply - vested - emitted - coalesce(tokens.stake_pool, 0))/power(10, decimals) as market_cap
                , (current_total_supply - vested - emitted - coalesce(tokens.stake_pool, 0))/power(10, decimals) as in_circulation
            from tokens
            where token_id = :token_id
        ''')
        with engDanaides.begin() as con:
            res = con.execute(sql, {'token_id': token_id}).fetchone()

        return res['in_circulation']
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid paideiaInCirculation request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid paideiaInCirculation request ({e})')


# request by CMC/coingecko (3/7/2022)
@r.get("/ergopadInCirculation", name="blockchain:ergopadInCirculation")
async def ergopadInCirculation():
    try:
        token_id = 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413'
        sql = text(f'''
            select token_name
                , token_id
                , token_price
                , current_total_supply/power(10, decimals) as current_total_supply
                , emission_amount/power(10, decimals) as initial_total_supply
                , (emission_amount - current_total_supply)/power(10, decimals) as burned
                , token_price * (current_total_supply - vested - emitted - coalesce(tokens.stake_pool, 0))/power(10, decimals) as market_cap
                , (current_total_supply - vested - emitted - coalesce(tokens.stake_pool, 0))/power(10, decimals) as in_circulation
            from tokens
            where token_id = :token_id
        ''')
        with engDanaides.begin() as con:
            res = con.execute(sql, {'token_id': token_id}).fetchone()

        return res['in_circulation']
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid ergopadInCirculation request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid ergopadInCirculation request ({e})')


# request by CMC/coingecko (3/7/2022)
@r.get("/totalSupply/{tokenId}", name="blockchain:totalSupply")
async def totalSupply(tokenId):
    # check cache
    cached = cache.get(f"get_api_blockchain_total_supply_{tokenId}")
    if cached:
        logging.debug(f'CACHED_TOTAL_SUPPLY_{tokenId}: {cached}')
        return cached
    try:
        sqlTokenomics = text(f'''
			select token_name
                , token_id
                , token_price
                , supply_actual
                , emission_amount_actual
                , emission_amount_actual - supply_actual as burned
                , token_price * in_circulation_actual as market_cap
                , in_circulation_actual
            from tokenomics_ergopad
        ''')
        res = engDanaides.execute(sqlTokenomics, {'token_id': tokenId}).fetchone()
        totalSupply = res['supply_actual']

        # set cache
        cache.set(f"get_api_blockchain_total_supply_{tokenId}", totalSupply) # default 15 min TTL
        return totalSupply
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid totalSupply request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid totalSupply request ({e})')


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


def getNFTBox(tokenId: str, allowCached=False, includeMempool=True):
    try:
        if includeMempool:
            ok = False
            memResContent = None
            if allowCached:
                # allowCached is true for snapshots
                cached = cache.get("get_explorer_mempool_boxes_unspent")
                if cached:
                    ok = cached["ok"]
                    memResContent = cached["memResContent"] 
                else:
                    # same api hit independent of token id
                    # cache for 5 mins for snapshots only
                    memRes = requests.get(f'{CFG.explorer}/mempool/boxes/unspent')
                    ok = memRes.ok
                    if ok:
                        memResContent = memRes.content.decode('utf-8')
                    content = {
                        "ok": ok,
                        "memResContent": memResContent
                    }
                    cache.set("get_explorer_mempool_boxes_unspent", content, 600) # 10 mins
            else:
                # if cached is not allowed force api call
                memRes = requests.get(f'{CFG.explorer}/mempool/boxes/unspent')
                ok = memRes.ok
                if ok:
                    memResContent = memRes.content.decode('utf-8')
                
            if ok:
                memResJson = []
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
                    if "assets" in memBox:
                        for token in memBox["assets"]:
                            if token["tokenId"]==tokenId:
                                return memBox
        res = requests.get(f'{CFG.explorer}/boxes/unspent/byTokenId/{tokenId}')
        logging.debug('Explorer api call: return from boxes/unspent/byTokenId')
        if res.ok:
            items = res.json()["items"]
            if len(items) == 1:
                return items[0]
            else:
                logging.error(f'ERR:{myself()}: multiple nft box or tokenId doesn\'t exist')

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find nft box ({e})')
        return None
 

@r.get("/signingRequest/{txId}", name="blockchain:signingRequest")
def signingRequest(txId):
    return cache.get(f'ergopay_signing_request_{txId}')


# @r.get("/getUnspentBoxesByTokenId/{tokenId}", name='blockchain:getUnspentBoxesByTokenId')
def getUnspentBoxesByTokenId(tokenId, useExplorerApi=False):
    try:
        # # is this a valid token/avoid sql injection attack
        # try: 
        #     if int(tokenId, 16) && (len(tokenId) == 64):
        #         sql = f'''
        #             select box_id, registers::json
        #             from utxos
        #             where assets->{tokenId!r} is not null
        #         '''
        #         with engDanaides.begin() as con:
        #             res = con.execute(sql, {}).fetchall()
        #         boxes = []
        #         for data in res:
        #             boxes.append({ 
        #                 'boxId': data["box_id"],
        #                 'additionalRegisters': data["additional_registers"],
        #             })
        #    
        #         return boxes
        #
        #     else:
        #         return {}
        # 
        # except ValueError as e: 
        #     logging.error(f'ERR:{myself()}: invalid token id ({e})')
        #     return {}
        #
        # except Exception as e:
        #     logging.error(f'ERR:{myself()}: failed to get boxes by token id ({e})')
        #     return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: failed to get boxes by token id ({e})')

        if not useExplorerApi:
            con = create_engine(EXPLORER)
            sql = f"""    
                select
                    o.box_id as box_id
                    , o.additional_registers as additional_registers
                from node_outputs o
                    left join node_inputs i on i.box_id = o.box_id
                    join node_assets a on a.box_id = o.box_id
                        and a.header_id = o.header_id
                where
                    o.main_chain = true
                    and i.box_id is null -- output with no input = unspent
                    and a.token_id = {tokenId!r}
            """
            res = con.execute(sql).fetchall()
            boxes = []
            for data in res:
                boxes.append({ 
                    'boxId': data["box_id"],
                    'additionalRegisters': data["additional_registers"],
                })

            return boxes
        
        # not implemented
        else:
            return {}

    except Exception as e:
        logging.error(f'ERR:{myself()}: failed to get boxes by token id ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: failed to get boxes by token id ({e})')


# GET unspent stake boxes
# Note: Run with useExplorerApi = True in case local explorer service failure
def getUnspentStakeBoxes(stakeTokenId: str = STAKE_KEY_ID, stakeAddress: str = STAKE_ADDRESS, useExplorerApi=False):
    if useExplorerApi:
        # slow, makes 10+ api calls each taking 1 to 1.5 seconds on average
        boxes = []
        offset = 0
        limit = 100
        done = False
        while not done:
            res = getTokenBoxes(stakeTokenId, offset, limit)
            boxes.extend(res)
            offset += limit
            if len(res) < limit:
                done = True
        return boxes
    else:
        # fast, average response time around 3 seconds
        return getUnspentStakeBoxesFromExplorerDB(stakeTokenId, stakeAddress)


# GET unspent boxes by token id direct from explorer db
def getUnspentStakeBoxesFromExplorerDB(stakeTokenId: str = STAKE_KEY_ID, stakeAddress: str = STAKE_ADDRESS):
    try:
        con = create_engine(EXPLORER)
        sql = f"""
            -- /unspent/byTokenId (optimized for stakeTokenId)
            select
                o.box_id as box_id,
                -- additional registers in JSON format
                -- R4 penalty
                -- R5 stake key
                o.additional_registers as additional_registers,
                -- erg value
                o.value as value,
                -- address
                o.address as address,
                a.token_id as token_id,
                -- index of the token in assets list
                -- 0 stake token
                -- 1 ergopad staked
                a.index as index,
                -- amount of token in the box
                a.value as token_value
            from
                node_outputs o
                join node_assets a on a.box_id = o.box_id
                and a.header_id = o.header_id
            where
                o.box_id in (
                    -- sub query to get unspent box ids
                    -- non correlated sub query => executed once
                    select
                        o.box_id as box_id
                    from
                        node_outputs o
                        left join node_inputs i on i.box_id = o.box_id
                        join node_assets a on a.box_id = o.box_id
                        and a.header_id = o.header_id
                    where
                        o.main_chain = true
                        and o.address = {stakeAddress!r} -- all stake boxes are for this address
                        and i.box_id is null -- output with no input = unspent
                        and a.token_id = {stakeTokenId!r} -- stake key token id
                        and coalesce(a.value, 0) > 0
                );
        """
        res = con.execute(sql).fetchall()
        boxes = {}
        for data in res:
            if data["box_id"] in boxes:
                boxes[data["box_id"]]["assets"].insert(data["index"], {"tokenId": data["token_id"], "index": data["index"], "amount": data["token_value"]})
            else:
                boxes[data["box_id"]] = {
                    "boxId": data["box_id"],
                    "additionalRegisters": data["additional_registers"],
                    "address": data["address"],
                    "value": data["value"],
                    "assets": [{"tokenId": data["token_id"], "index": data["index"], "amount": data["token_value"]}]
                }
        return list(boxes.values())
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: failed to read data from explorer db ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: failed to read data from explorer db ({e})')


# GET token boxes legacy code using explorer API
def getTokenBoxes(tokenId: str, offset: int = 0, limit: int = 100, retries: int = 10):
    try:
        while retries > 0:
            res = requests.get(f'{CFG.explorer}/boxes/unspent/byTokenId/{tokenId}?offset={offset}&limit={limit}')
            if res.ok:
                items = res.json()["items"]
                return items
            else:
                if res.status_code == 503:
                    retries -= 1
                else:
                    retries = 0
        raise Exception("Explorer not responding correctly")    
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find token box ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find token box ({e})')


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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find unspent tokens ({e})')


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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to build script ({e})')


class AirdropRequest(BaseModel):
    tokenId: str
    submit: bool = False
    addresses: Dict[str,Decimal]


@r.post("/airdrop", name="blockchain:airdrop")
async def airdrop( 
    req: AirdropRequest,
    current_user=Depends(get_current_active_superuser)
):
    appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/",CFG.ergopadApiKey)
    airdropTokenInfo = getTokenInfo(req.tokenId)
    nErgRequired = 0
    tokensRequired = 0
    outputs = []
    for address in req.addresses.keys():
        tokenAmount = int(req.addresses[address]*10**airdropTokenInfo["decimals"])
        tokensRequired += tokenAmount
        nErgRequired += int(1e6)
        outputs.append(appKit.buildOutBox(
            value=int(1e6),
            tokens={
                req.tokenId: tokenAmount
            },
            registers=None,
            contract=appKit.contractFromAddress(address)
        ))
    
    feeRequired = max(int(1e6),int(len(outputs)*int(1e5)))
    inputs = appKit.boxesToSpend(CFG.ergopadWallet,nErgRequired+feeRequired,{req.tokenId: tokensRequired})
    unsignedTx = appKit.buildUnsignedTransaction(
        inputs=inputs,
        outputs=outputs,
        fee=feeRequired,
        sendChangeTo=appKit.contractFromAddress(CFG.ergopadWallet).toAddress().getErgoAddress()
    )
    signedTx = appKit.signTransactionWithNode(unsignedTx)

    if req.submit:
        return appKit.sendTransaction(signedTx)
    
    return ErgoAppKit.unsignedTxToJson(unsignedTx)


@r.get("/tvl/{tokenId}", name="blockchain:tvl")
async def tvl(tokenId: str):
    try:
        cached = cache.get(f"get_tvl_{tokenId}")
        if cached:
            return cached
        else:
            sqlStaking = text(f'''
                select s.token_id, sum(s.amount * t.token_price) as tvl
                from staking s
                    join tokens t on t.token_id = s.token_id
                where s.token_id = :token_id
                group by s.token_id
            ''')

            sqlVesting = text(f'''
                with assets as (
                    select (each(assets)).key::varchar(64) as token_id
                        , (each(assets)).value::bigint as amount
                    from utxos
                    where ergo_tree in (
                        -- vestingAddress = "Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp"
                        '10070400040204000500040004000400d80bd601e4c6a7040ed602b2db6308a7730000d6038c720201d604e4c6a70805d605e4c6a70705d606e4c6a70505d607e4c6a70605d6089c9d99db6903db6503fe720572067207d6098c720202d60a9972047209d60b958f99720472087207997204720a997208720ad1ed93b0b5a5d9010c63ededed93c2720c720193e4c6720c040ee4c6a7090e93b1db6308720c7301938cb2db6308720c7302000172037303d9010c41639a8c720c018cb2db63088c720c0273040002720bec937209720baea5d9010c63ededededededededed93c1720cc1a793c2720cc2a7938cb2db6308720c730500017203938cb2db6308720c73060002997209720b93e4c6720c040e720193e4c6720c0505720693e4c6720c0605720793e4c6720c0705720593e4c6720c0805720493e4c6720c090ee4c6a7090e'
                        -- vestingWithNFTAddress = "2k6J5ocjeESe4cuXP6rwwq55t6cUwiyqDzNdEFgnKhwnWhttnSShZb4LaMmqTndrog6MbdT8iJbnnwWEcNoeRfEqXBQW4ohBTgm8rDnu9WBBZSixjJoKPT4DStGSobBkoxS4HZMe4brCgujdnmnMBNf8s4cfGtJsxRqGwtLMvmP6Z6FAXw5pYveHRFDBZkhh6qbqoetEKX7ER2kJormhK266bPDQPmFCcsoYRdRiUJBtLoQ3fq4C6N2Mtb3Jab4yqjvjLB7JRTP82wzsXNNbjUsvgCc4wibpMc8MqJutkh7t6trkLmcaH12mAZBWiVhwHkCYCjPFcZZDbr7xeh29UDcwPQdApxHyrWTWHtNRvm9dpwMRjnG2niddbZU82Rpy33cMcN3cEYZajWgDnDKtrtpExC2MWSMCx5ky3t8C1CRtjQYX2yp3x6ZCRxG7vyV7UmfDHWgh9bvU"
                        , '100e04020400040404000402040604000402040204000400040404000400d810d601b2a4730000d602e4c6a7050ed603b2db6308a7730100d6048c720302d605e4c6a70411d6069d99db6903db6503feb27205730200b27205730300d607b27205730400d608b27205730500d6099972087204d60a9592720672079972087209999d9c7206720872077209d60b937204720ad60c95720bb2a5730600b2a5730700d60ddb6308720cd60eb2720d730800d60f8c720301d610b2a5730900d1eded96830201aedb63087201d901114d0e938c721101720293c5b2a4730a00c5a79683050193c2720cc2720193b1720d730b938cb2720d730c00017202938c720e01720f938c720e02720aec720bd801d611b2db63087210730d009683060193c17210c1a793c27210c2a7938c721101720f938c721102997204720a93e4c67210050e720293e4c6721004117205'
                    )
                )
                select a.token_id, sum((a.amount/power(10, coalesce(t.decimals, 0))) * coalesce(t.token_price, 0.0)) as tvl
                from assets a
                    left join tokens t on t.token_id = a.token_id
                where a.token_id = :token_id
                group by a.token_id
            ''')

            # engDanaides = create_engine(CFG.csDanaides)
            with engDanaides.begin() as con:
                resStaking = con.execute(sqlStaking, {'token_id': tokenId}).fetchone()
                resVesting = con.execute(sqlVesting, {'token_id': tokenId}).fetchone()

            stakingTVL = resStaking['tvl'] or 0
            vestingTVL = resVesting['tvl'] or 0

            result = {
                'tvl': {
                    'total': stakingTVL + vestingTVL,
                    'staked': stakingTVL,
                    'vested': vestingTVL
                }
            }
            cache.set(f"get_tvl_{tokenId}",result)

            return result

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to determine TVL ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to determine TVL.')

#endregion ROUTES
