from decimal import Decimal
from enum import Enum
from typing import Dict
from xmlrpc.client import Boolean
import requests, json
from core.auth import get_current_active_superuser
from ergo.appkit import ErgoAppKit
from wallet import Wallet

from sqlalchemy import create_engine
from starlette.responses import JSONResponse
from fastapi import APIRouter, Depends, status
from time import time
from api.v1.routes.asset import get_asset_current_price
from cache.cache import cache
from config import Config, Network # api specific config
from pydantic import BaseModel

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
DATABASE = CFG.connectionString
EXPLORER = CFG.csExplorer
STAKE_ADDRESS = '3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9'
STAKE_KEY_ID = '1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee'

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

        # stake pool
        sqlPooled = f"""
			select coalesce(sum(a.value)/max(power(10, t.decimals)), 0) as "stakePool"
            from node_outputs o
                left join node_inputs i on o.box_id = i.box_id
                	and i.main_chain = true
                join node_assets a on a.box_id = o.box_id
				join tokens t on t.token_id = a.token_id
            where o.main_chain = true
                and i.box_id is null -- output with no input == unspent
                and o.address = '9hXmgvzndtakdSAgJ92fQ8ZjuKirWAw8tyDuyJrXP6sKHVpCz8XbMANK3BVJ1k3WD6ovQKTCasjKL5WMncRB6V9HvmMnJ2WbxYYjtLFS9sifDNXJWugrNEgoVK887bR5oaLZA95yGkMeXVfanxpNDZYaXH9KpHCpC5ohDtaW1PF17b27559toGVCeCUNti7LXyXV8fWS1mVRuz2PhLq5mB7hg2bqn7CZtVM8ntbUJpjkHUc9cP1R8Gvbo1GqcNWgM7gZkr2Dp514BrFz1cXMkv7TYEqH3cdxX9c82hH6fdaf3n6avdtZ5bgqerUZVDDW6ZsqxrqTyTMQUUirRAi3odmMGmuMqDJbU3Z1VnCF9NBow7jrKUDSgckDZakFZNChsr5Kq1kQyNitYJUh9fra1jLHCQ9yekz3te9E'
                and coalesce(o.value, 0) > 0
        """
        res = con.execute(sqlPooled).fetchone()
        stakePool = res['stakePool']

        # emission box
        sqlEmitted = f"""
			select coalesce(sum(a.value)/max(power(10, t.decimals)), 0) as "emitted"
            from node_outputs o
                left join node_inputs i on o.box_id = i.box_id
                	and i.main_chain = true
                join node_assets a on a.box_id = o.box_id
				join tokens t on t.token_id = a.token_id
            where o.main_chain = true
                and i.box_id is null -- output with no input == unspent
                and o.address = 'xhRNa2Wo7xXeoEKbLcsW4gV1ggBwrCeXVkkjwMwYk4CVjHo95CLDHmomXirb8SVVtovXNPuqcs6hNMXdPPtT6nigbAqei9djAnpDKsAvhk5M4wwiKPf8d5sZFCMMGtthBzUruKumUW8WTLXtPupD5jBPELekR6yY4zHV4y21xtn7jjeqcb9M39RLRuFWFq2fGWbu5PQhFhUPCB5cbxBKWWxtNv8BQTeYj8bLw5vAH1WmRJ7Ln7SfD9RVePyvKdWGSkTFfVtg8dWuVzEjiXhUHVoeDcdPhGftMxWVPRZKRuMEmYbeaxLyccujuSZPPWSbnA2Uz6EketQgHxfnYhcLNnwNPaMETLKtvwZygfk1PuU9LZPbxNXNFgHuujfXGfQbgNwgd1hcC8utB6uZZRbxXAHmgMaWuoeSsni99idRHQFHTkmTKXx4TAx1kGKft1BjV6vcz1jGBJQyFBbQCTYBNcm9Yq2NbXmk5Vr7gHYbKbig7eMRT4oYxZdb9rwupphRGK4b2tYis9dXMT8m5EfFzxvAY9Thjbg8tZtWX7F5eaNzMKmZACZZqW3U7qS6aF8Jgiu2gdK12QKKBTdBfxaC6hBVtsxtQXYYjKzCmq1JuGP1brycwCfUmTUFkrfNDWBnrrmF2vrzZqL6WtUaSHzXzC4P4h346xnSvrtTTx7JGbrRCxhsaqTgxeCBMXgKgPGud2kNvgyKbjKnPvfhSCYnwhSdZYj8R1rr4TH5XjB3Wv8Z4jQjCkhAFGWJqVASZ3QXrFGFJzQrGLL1XX6cZsAP8cRHxqa7tJfKJzwcub7RjELPa2nnhhz5zj5F9MU1stJY4SBiX3oZJ6HdP9kNFGMR86Q6Z5qyfSRjwDNjVyvkKNoJ6Yk9nm367gznSVWkS9SG3kCUonbLgRt1Moq7o9CN5KrnyRgLrEAQU83SGY7Bc6FcLCZqQn8VqxP4e8R3vhf24nrzXVopydiYai'
                and coalesce(o.value, 0) > 0
        """
        res = con.execute(sqlEmitted).fetchone()
        emitted = res['emitted']

        sqlVested = f"""
			select coalesce(sum(a.value)/max(power(10, t.decimals)), 0) as "vested"
            from node_outputs o
                left join node_inputs i on o.box_id = i.box_id
                	and i.main_chain = true
                join node_assets a on a.box_id = o.box_id
				join tokens t on t.token_id = a.token_id
            where o.main_chain = true
                and i.box_id is null -- output with no input == unspent
                and o.address = 'Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp'
                and coalesce(o.value, 0) > 0
        """
        res = con.execute(sqlVested).fetchone()
        vested = res['vested']

        # find vested
        sqlStaked = f"""
			select coalesce(sum(a.value)/max(power(10, t.decimals)), 0) as "staked"
            from node_outputs o
                left join node_inputs i on o.box_id = i.box_id
                	and i.main_chain = true
                join node_assets a on a.box_id = o.box_id
				join tokens t on t.token_id = a.token_id
            where o.main_chain = true
                and i.box_id is null -- output with no input == unspent
                and o.address = '3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9'
                and coalesce(o.value, 0) > 0
        """
        res = con.execute(sqlStaked).fetchone()
        staked = res['staked']

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
                and a.token_id = '{tokenId}'
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

def getNFTBox(tokenId: str, allowCached=False):
    try:
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
                    and a.token_id = '{tokenId}'
            """
            res = con.execute(sql).fetchall()
            boxes = {}
            for data in res:
                boxes[data["box_id"]] = data["additional_registers"]
                    
            return list(boxes.values())
        
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
                        and o.address = '{STAKE_ADDRESS}' -- all stake boxes are for this address
                        and i.box_id is null -- output with no input = unspent
                        and a.token_id = '{STAKE_KEY_ID}' -- stake key token id
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

        res = requests.get(f'http://52.12.102.149:9053/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': '49eCcDzqLzL5Gams'}))
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
    appKit = ErgoAppKit(CFG.node,Network,CFG.explorer + "/")
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
    
    return appKit.unsignedTxToJson(unsignedTx)

#endregion ROUTES

### MAIN
if __name__ == '__main__':
    print('API routes: ...')