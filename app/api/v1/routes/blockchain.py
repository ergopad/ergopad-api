from decimal import Decimal
from enum import Enum
from typing import Dict
from xmlrpc.client import Boolean
import requests, json
from core.auth import get_current_active_superuser
from ergo_python_appkit.appkit import ErgoAppKit
from wallet import Wallet

from sqlalchemy import create_engine
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

    buyerWallet        = Wallet('9iLSsvi2zobapQmi7tXVK4mnrbQwpK3oTfPcCpF9n7J2DQVpxq2') # simulate buyer / seed tokens

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

        # nodeInfo['vestingBegin_ms'] = f'{ctime(1643245200)} UTC'
        nodeInfo['sigUSD'] = await get_asset_current_price('sigusd')
        nodeInfo['inDebugMode'] = ('PROD', '!! DEBUG !!')[DEBUG]

        logging.debug(f'::TOOK {time()-st:0.4f}s')
        return nodeInfo

    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid blockchain info ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid blockchain info ({e})')

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
    # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
    try:
        tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
        return tkn.json()
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
@r.get("/emissionAmount/{tokenId}", name="blockchain:emissionAmount")
def getEmmissionAmount(tokenId):
    try:
        tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
        decimals = tkn.json()['decimals']
        emissionAmount = tkn.json()['emissionAmount'] / 10**decimals
        return emissionAmount
        
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
        # con = create_engine(EXPLORER)
        sql = f"""
            with 
            -- ignore duplicate unspent box_ids
            unspent as (
                select o.box_id
                from node_outputs o 
                    left join node_inputs i on o.box_id = i.box_id
                        and i.main_chain = true
                where i.box_id is null
                    and o.address = {address!r}
                    and o.main_chain = true
                    and coalesce(o.value, 0) > 0
                group by o.box_id
            )
            -- ignore null and duplicate values
            , assets as (
                select max(a.value) as value, max(a.token_id) as token_id, a.box_id
                from node_assets a
                    join unspent u on u.box_id = a.box_id
                group by a.box_id
            )
            -- find decimals
            , tokens as (
                select token_id, decimals
                from tokens
                where token_id = {token_id!r}
            )
            select sum(a.value)/max(power(10, t.decimals)) as "res"
            from unspent u
                join assets a on a.box_id = u.box_id
                join tokens t on t.token_id = a.token_id
        """
        res = con.execute(sql).fetchone()
        return res['res']
    except:
        return 0

# paideia tokenId: 1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489
@r.get("/paideiaInCirculation", name="blockchain:paideiaInCirculation")
def paideiaInCirculation():
    # check cache
    cached = cache.get("get_api_blockchain_paideia_in_circulation")
    if cached:
        logging.debug(f'CACHED_PAIDEIA_IN_CIRC: {cached}')
        return cached
    try:
        con = create_engine(EXPLORER)
        supply = totalSupply('1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489')
        logging.debug(f'TOTAL_SUPPLY_PAIDEIA_IN_CIRC: {supply}')

        token_id = '1fd6e032e8476c4aa54c18c1a308dce83940e8f4a28f576440513ed7326ad489'

        stakePool = 0

        address = '2k6J5ocjeESe4cuXP6rwwq55t6cUwiyqDzNdEFgnKhwnWhttnSShZb4LaMmqTndrog6MbdT8iJbnnwWEcNoeRfEqXBQW4ohBTgm8rDnu9WBBZSixjJoKPT4DStGSobBkoxS4HZMe4brCgujdnmnMBNf8s4cfGtJsxRqGwtLMvmP6Z6FAXw5pYveHRFDBZkhh6qbqoetEKX7ER2kJormhK266bPDQPmFCcsoYRdRiUJBtLoQ3fq4C6N2Mtb3Jab4yqjvjLB7JRTP82wzsXNNbjUsvgCc4wibpMc8MqJutkh7t6trkLmcaH12mAZBWiVhwHkCYCjPFcZZDbr7xeh29UDcwPQdApxHyrWTWHtNRvm9dpwMRjnG2niddbZU82Rpy33cMcN3cEYZajWgDnDKtrtpExC2MWSMCx5ky3t8C1CRtjQYX2yp3x6ZCRxG7vyV7UmfDHWgh9bvU'
        vested  = sqlTokenValue(address, token_id, con)
        logging.debug(f'paideia vested: {vested}')

        reserved = 0

        emitted = 0

        paideiaInCirculation = supply - stakePool - vested - reserved - emitted

        # set cache
        cache.set("get_api_blockchain_paideia_in_circulation", paideiaInCirculation) # default 15 min TTL
        return paideiaInCirculation
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid paideiaInCirculation request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid paideiaInCirculation request ({e})')

# request by CMC/coingecko (3/7/2022)
@r.get("/ergopadInCirculation", name="blockchain:ergopadInCirculation")
def ergopadInCirculation():
    # check cache
    cached = cache.get("get_api_blockchain_ergopad_in_circulation")
    if cached:
        return cached
    try:
        con = create_engine(EXPLORER)
        supply = totalSupply('d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413')

        # don't currently use this, but may be useful to have
        burned = 400*(10**6) - supply

        token_id = 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413'

        address = '9hXmgvzndtakdSAgJ92fQ8ZjuKirWAw8tyDuyJrXP6sKHVpCz8XbMANK3BVJ1k3WD6ovQKTCasjKL5WMncRB6V9HvmMnJ2WbxYYjtLFS9sifDNXJWugrNEgoVK887bR5oaLZA95yGkMeXVfanxpNDZYaXH9KpHCpC5ohDtaW1PF17b27559toGVCeCUNti7LXyXV8fWS1mVRuz2PhLq5mB7hg2bqn7CZtVM8ntbUJpjkHUc9cP1R8Gvbo1GqcNWgM7gZkr2Dp514BrFz1cXMkv7TYEqH3cdxX9c82hH6fdaf3n6avdtZ5bgqerUZVDDW6ZsqxrqTyTMQUUirRAi3odmMGmuMqDJbU3Z1VnCF9NBow7jrKUDSgckDZakFZNChsr5Kq1kQyNitYJUh9fra1jLHCQ9yekz3te9E'
        stakePool = sqlTokenValue(address, token_id, con)
        logging.debug(f'ergopad stakePool: {stakePool}')

        address = 'xhRNa2Wo7xXeoEKbLcsW4gV1ggBwrCeXVkkjwMwYk4CVjHo95CLDHmomXirb8SVVtovXNPuqcs6hNMXdPPtT6nigbAqei9djAnpDKsAvhk5M4wwiKPf8d5sZFCMMGtthBzUruKumUW8WTLXtPupD5jBPELekR6yY4zHV4y21xtn7jjeqcb9M39RLRuFWFq2fGWbu5PQhFhUPCB5cbxBKWWxtNv8BQTeYj8bLw5vAH1WmRJ7Ln7SfD9RVePyvKdWGSkTFfVtg8dWuVzEjiXhUHVoeDcdPhGftMxWVPRZKRuMEmYbeaxLyccujuSZPPWSbnA2Uz6EketQgHxfnYhcLNnwNPaMETLKtvwZygfk1PuU9LZPbxNXNFgHuujfXGfQbgNwgd1hcC8utB6uZZRbxXAHmgMaWuoeSsni99idRHQFHTkmTKXx4TAx1kGKft1BjV6vcz1jGBJQyFBbQCTYBNcm9Yq2NbXmk5Vr7gHYbKbig7eMRT4oYxZdb9rwupphRGK4b2tYis9dXMT8m5EfFzxvAY9Thjbg8tZtWX7F5eaNzMKmZACZZqW3U7qS6aF8Jgiu2gdK12QKKBTdBfxaC6hBVtsxtQXYYjKzCmq1JuGP1brycwCfUmTUFkrfNDWBnrrmF2vrzZqL6WtUaSHzXzC4P4h346xnSvrtTTx7JGbrRCxhsaqTgxeCBMXgKgPGud2kNvgyKbjKnPvfhSCYnwhSdZYj8R1rr4TH5XjB3Wv8Z4jQjCkhAFGWJqVASZ3QXrFGFJzQrGLL1XX6cZsAP8cRHxqa7tJfKJzwcub7RjELPa2nnhhz5zj5F9MU1stJY4SBiX3oZJ6HdP9kNFGMR86Q6Z5qyfSRjwDNjVyvkKNoJ6Yk9nm367gznSVWkS9SG3kCUonbLgRt1Moq7o9CN5KrnyRgLrEAQU83SGY7Bc6FcLCZqQn8VqxP4e8R3vhf24nrzXVopydiYai'
        emitted = sqlTokenValue(address, token_id, con)
        logging.debug(f'ergopad emitted: {emitted}')

        address = 'Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp'
        vested  = sqlTokenValue(address, token_id, con)
        logging.debug(f'ergopad vested: {vested}')

        address = '3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9'
        staked  = sqlTokenValue(address, token_id, con)
        logging.debug(f'ergopad staked: {staked}')

        reserved = 20*(10**6) # 20M in reserve wallet, 9ehADYzAkYzUzQHqwM5KqxXwKAnVvkL5geSkmUzK51ofj2dq7K8
        ergopadInCirculation = supply - stakePool - vested - reserved - emitted

        # set cache
        cache.set("get_api_blockchain_ergopad_in_circulation", ergopadInCirculation) # default 15 min TTL
        return ergopadInCirculation
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid ergopadInCirculation request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid ergopadInCirculation request ({e})')

# request by CMC/coingecko (3/7/2022)
@r.get("/totalSupply/{tokenId}", name="blockchain:totalSupply")
def totalSupply(tokenId):
    # check cache
    cached = cache.get(f"get_api_blockchain_total_supply_{tokenId}")
    if cached:
        return cached
    try:
        # NOTE: total emmission doesn't account for burned tokens, which recently began to happen (accidentally so far)
        # ergopad: d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413
        con = create_engine(EXPLORER)
        sqlTotalSupply = f"""
            select 
                -- filter to "unspent", giving "current" view; avoid nulls
                coalesce(sum(a.value)/max(power(10, t.decimals)), 0) as "totalSupply"

            from node_outputs o

                -- "burned" / invalidate any box that doesn't have an input
                left join node_inputs i on o.box_id = i.box_id
                	-- and i.main_chain = true -- ?? is this necessary/useful

                -- find the proper asset
                join node_assets a on a.box_id = o.box_id
                    and a.header_id = o.header_id
				
                -- find decimals for the token
                join tokens t on t.token_id = a.token_id
                
            where o.main_chain = true
                and i.box_id is null -- output with no input == unspent
                and a.token_id = {tokenId!r}
                and coalesce(a.value, 0) > 0 -- ignore nulls
        """
        res = con.execute(sqlTotalSupply).fetchone()
        totalSupply = res['totalSupply']

        # set cache
        cache.set(f"get_api_blockchain_total_supply_{tokenId}", totalSupply) # default 15 min TTL
        return totalSupply
        
    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid totalSupply request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid totalSupply request ({e})')

# assember follow info
@r.get("/followInfo/{followId}", name="blockchain:followInfo")
def followInfo(followId):
    try:
        res = requests.get(f'{CFG.assembler}/result/{followId}')
        return res.json()

    except Exception as e:
        logging.error(f'ERR:{myself()}: invalid assembly follow ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: invalid assembly follow ({e})')

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
def getUnspentStakeBoxes(useExplorerApi=False):
    if useExplorerApi:
        # slow, makes 10+ api calls each taking 1 to 1.5 seconds on average
        boxes = []
        offset = 0
        limit = 100
        done = False
        while not done:
            res = getTokenBoxes(STAKE_KEY_ID, offset, limit)
            boxes.extend(res)
            offset += limit
            if len(res) < limit:
                done = True
        return boxes
    else:
        # fast, average response time around 3 seconds
        return getUnspentStakeBoxesFromExplorerDB()

# GET unspent boxes by token id direct from explorer db
def getUnspentStakeBoxesFromExplorerDB():
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
                        and o.address = {STAKE_ADDRESS!r} -- all stake boxes are for this address
                        and i.box_id is null -- output with no input = unspent
                        and a.token_id = {STAKE_KEY_ID!r} -- stake key token id
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
def getTokenBoxes(tokenId: str, offset: int = 0, limit: int = 100):
    try:
        res = requests.get(f'{CFG.explorer}/boxes/unspent/byTokenId/{tokenId}?offset={offset}&limit={limit}')
        if res.ok:
            items = res.json()["items"]
            return items
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

# find unspent boxes with tokens
def getBoxesWithUnspentTokens_beta(nErgAmount=-1, tokenId=CFG.ergopadTokenId, tokenAmount=-1, allowMempool=True, emptyRegisters=False):
    try:
        foundTokenAmount = 0
        foundNErgAmount = 0
        ergopadTokenBoxes = {}

        # res = requests.get(f'http://52.12.102.149:9053/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': '49eCcDzqLzL5Gams'}))
        res = requests.get(f'{ergopadNode}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': '49eCcDzqLzL5Gams'}))
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
        logging.error(f'ERR:{myself()}: BETA/unable to find unspent tokens ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: BETA/unable to find unspent tokens ({e})')


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
    
    cached = cache.get(f"get_tvl_{tokenId}")
    if cached:
        return cached
    else:
        stakingAddress = "3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9"
        vestingAddress = "Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp"
        vestingWithNFTAddress = "2k6J5ocjeESe4cuXP6rwwq55t6cUwiyqDzNdEFgnKhwnWhttnSShZb4LaMmqTndrog6MbdT8iJbnnwWEcNoeRfEqXBQW4ohBTgm8rDnu9WBBZSixjJoKPT4DStGSobBkoxS4HZMe4brCgujdnmnMBNf8s4cfGtJsxRqGwtLMvmP6Z6FAXw5pYveHRFDBZkhh6qbqoetEKX7ER2kJormhK266bPDQPmFCcsoYRdRiUJBtLoQ3fq4C6N2Mtb3Jab4yqjvjLB7JRTP82wzsXNNbjUsvgCc4wibpMc8MqJutkh7t6trkLmcaH12mAZBWiVhwHkCYCjPFcZZDbr7xeh29UDcwPQdApxHyrWTWHtNRvm9dpwMRjnG2niddbZU82Rpy33cMcN3cEYZajWgDnDKtrtpExC2MWSMCx5ky3t8C1CRtjQYX2yp3x6ZCRxG7vyV7UmfDHWgh9bvU"
        
        stakingBalanceC = get_asset_balance_from_address(stakingAddress)
        vestingBalanceC = get_asset_balance_from_address(vestingAddress)
        vestingWithNFTBalanceC = get_asset_balance_from_address(vestingWithNFTAddress)

        stakingBalance = await stakingBalanceC
        vestingBalance = await vestingBalanceC
        vestingWithNFTBalance = await vestingWithNFTBalanceC

        stakingTVL = 0
        for token in stakingBalance["balance"]["ERG"]["tokens"]:
            if token["tokenId"] == tokenId:
                stakingTVL += round(token["amount"]*10**(-1*token["decimals"])*token["price"],2)

        vestingTVL = 0
        for token in vestingBalance["balance"]["ERG"]["tokens"] + vestingWithNFTBalance["balance"]["ERG"]["tokens"]:
            if token["tokenId"] == tokenId:
                vestingTVL += round(token["amount"]*10**(-1*token["decimals"])*token["price"],2)
        result = {
            'tvl': {
                'total': stakingTVL + vestingTVL,
                'staked': stakingTVL,
                'vested': vestingTVL
            }
        }
        cache.set(f"get_tvl_{tokenId}",result)

        return result

#endregion ROUTES

### MAIN
if __name__ == '__main__':
    print('API routes: ...')