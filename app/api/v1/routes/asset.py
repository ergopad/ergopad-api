import requests 
import typing as t

from sqlalchemy import create_engine
from starlette.responses import JSONResponse
from fastapi import APIRouter, status
from fastapi import Path
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.sql.schema import BLANK_SCHEMA
from time import time
from datetime import datetime
from ergodex.price import getErgodexTokenPrice
from config import Config, Network # api specific config
from cache.cache import cache

CFG = Config[Network]

asset_router = r = APIRouter()

#region BLOCKHEADER
"""
Asset API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: Returns coin and token values by user, coin or wallet.

Notes: 
. Developed for ErgoHack II, October 2021
. TODO: intended to use reducers/redux model to improve testability/stability
. Replace APIs with database calls once data is populated (need supporting import scripts to maintain)
  - if keeping API calls, replace requests with async (i.e. httpx or aiohttp) to avoid blocking (requests is synchronous)
. ?? is this SigRSV? 003bd19d0187117f130b62e1bcab0939929ff5c7709f843c5c4dd158949285d0

Examples:
> http://localhost:8000/api/asset/user/hello
> http://localhost:8000/api/asset/price/cardano
> http://localhost:8000/api/asset/price/sigusd
> http://localhost:8000/api/asset/balance/9iD7JfYYemJgVz7nTGg9gaHuWg7hBbHo2kxrrJawyz4BD1r9fLS
> http://localhost:8000/api/asset/price/history/ergo/3

testnet: 3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG
mainnet: 9iD7JfYYemJgVz7nTGg9gaHuWg7hBbHo2kxrrJawyz4BD1r9fLS

"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

currency = 'usd' # TODO: store with user
total_sigrsv = 100000000000.01 # initial amount SigRSV
default_rsv_price = 1000000 # lower bound/default SigRSV value
nerg2erg = 1000000000.0 # 1e9 satoshis/kushtis in 1 erg
ergo_watch_api = CFG.ergoWatch
oracle_pool_url = CFG.oraclePool
coingecko_url = CFG.coinGecko
exchange = 'coinex'
symbol = 'ERG/USDT'

con = create_engine(CFG.connectionString)
#endregion INIT

#region LOGGING
import logging
level = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=level)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region ROUTES
#
# Single coin balance and tokens for wallet address
#
@r.get("/balance/{address}", name="asset:wallet-balance")
async def get_asset_balance_from_address(address: str = Path(..., min_length=40, regex="^[a-zA-Z0-9_-]+$")) -> None: 

    # get balance from ergo explorer api
    logging.debug(f'find balance for [blockchain], address: {address}...')
    res = requests.get(f'{CFG.ergoPlatform}/addresses/{address}/balance/total')    

    # handle invalid address or other error
    wallet_assets = {}
    balance = {}
    if res.status_code == 200:
        balance = res.json()
    # else:
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Something went wrong.")
    logging.info(f'Balance for ergo: {balance}')

    ergPrice = (await get_asset_current_price('ERGO'))['price']

    # handle SigUSD and SigRSV
    tokens = []
    for token in balance['confirmed']['tokens']:
        token['price'] = 0.0
        # if token['name'] == 'SigUSD': # TokenId: 22c6cc341518f4971e66bd118d601004053443ed3f91f50632d79936b90712e9
        if token['tokenId'] == '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04':
            price = (await get_asset_current_price('SigUSD'))['price']
            token['price'] = price
        # if token['name'] == 'SigRSV': # TokenId: 003bd19d0187117f130b62e1bcab0939929ff5c7709f843c5c4dd158949285d0
        if token['tokenId'] == '003bd19d0187117f130b62e1bcab0939929ff5c7709f843c5c4dd158949285d0':
            price = (await get_asset_current_price('SigRSV'))['price']
            token['price'] = price
        # Ergodex tokens
        # Lunadog    
        if token['tokenId'] == '5a34d53ca483924b9a6aa0c771f11888881b516a8d1a9cdc535d063fe26d065e':
            price = (await get_asset_current_price('LunaDog'))['price']
            token['price'] = price
        # Erdoge
        if token['tokenId'] == '36aba4b4a97b65be491cf9f5ca57b5408b0da8d0194f30ec8330d1e8946161c1':
            price = (await get_asset_current_price('Erdoge'))['price']
            token['price'] = price
        # NETA
        if token['tokenId'] == '472c3d4ecaa08fb7392ff041ee2e6af75f4a558810a74b28600549d5392810e8':
            price = (await get_asset_current_price('NETA'))['price']
            token['price'] = price
        # ergopad
        if token['tokenId'] == 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413':
            price = (await get_asset_current_price('ergopad'))['price']
            token['price'] = price
        tokens.append(token)

    # normalize result
    wallet_assets["ERG"] = {
        "blockchain": "ergo",
        "balance": balance['confirmed']['nanoErgs']/nerg2erg, # satoshis/kushtis
        "unconfirmed": balance['unconfirmed']['nanoErgs']/nerg2erg, # may not be available for all blockchains
        "tokens": tokens, # array
        "price": ergPrice,
    }
    # unconfirmed?

    return {
        "address": address,
        "balance": wallet_assets,
    }

#
# Find price by coin
# Base currency is USD for all coins and tokens.
# - Allow SigUSD/RSV ergo tokens to be listed as coins (TODO: change from ergo.watch api)
# - Allow multiple coins per blockchain (TODO: change from CoinGecko api)
#
@r.get("/price/{coin}", name="coin:coin-price")
async def get_asset_current_price(coin: str = None) -> None:
    coin = coin.lower()
    # check cache
    cached = cache.get(f"get_api_asset_price_{coin}")
    if cached:
        return cached

    price = 0.0  # init/default

    # SigUSD/SigRSV
    if coin in ('sigusd', 'sigrsv'):
        res = requests.get(ergo_watch_api).json()
        if res:
            if coin == 'sigusd':
                try:
                    # peg_rate_nano: current USD/ERG price [nanoERG]
                    # ERG/USD
                    ergo_price = (await get_asset_current_price("ergo"))["price"]
                    price = (res['peg_rate_nano'] / nerg2erg) * \
                        ergo_price  # SIGUSD
                except:
                    # if get_asset_current_price("ergo") fails
                    price = 1.0
            else:
                # calc for sigrsv
                # circ_sigusd: circulating SigUSD tokens in cents
                circ_sigusd = res['circ_sigusd']/100.0
                # peg_rate_nano: current USD/ERG price [nanoERG]
                peg_rate_nano = res['peg_rate_nano']
                # reserves: total amt in reserves [nanoERG]
                reserves = res['reserves']
                # liabilities in nanoERG's to cover stable coins in circulation
                # lower of reserves or SigUSD * SigUSD_in_circulation
                liabilities = min(circ_sigusd * peg_rate_nano, reserves)
                # find equity, at least 0
                equity = reserves - liabilities
                if equity < 0:
                    equity = 0
                if res['circ_sigrsv'] <= 1:
                    price = 0
                else:
                    price = (equity / res['circ_sigrsv']) / \
                        peg_rate_nano  # SigRSV/USD
    # ...all other prices
    else:
        price = None

        # first check ergodex
        logging.warning('find price from ergodex')
        ret = getErgodexTokenPrice(coin)
        if (ret["status"] == "success"):
            price = ret["price"]

        # check local database storage for price
        if price == None:
            logging.warning('find price from aggregator...')
            try:
                pairMapper = {
                    "ergo": "ERG/USDT",
                    "erg": "ERG/USDT",
                    "bitcoin": "BTC/USDT",
                    "btc": "BTC/USDT",
                    "ethereum": "ETH/USDT",
                    "eth": "ETH/USDT",
                } 
                sqlFindLatestPrice = f'select close from "{exchange}_{pairMapper[coin]}_1m" order by timestamp_utc desc limit 1'
                res = con.execute(sqlFindLatestPrice)
                price = res.fetchone()[0]
            except:
                pass

        # if not in local database, ask for online value
        if price == None:
            logging.warning('fallback to price from exchange')
            res = requests.get(f'{coingecko_url}/simple/price?vs_currencies={currency}&ids={coin}')
            try:
                price = res.json()[coin][currency] 
            except:
                pass

    ret = {
        "price": price
    }
    cache.set(f"get_api_asset_price_{coin}", ret)
    return ret


# Coin history response schema
class CoinHistoryDataPoint(BaseModel):
    timestamp: datetime
    price: float


class CoinHistory(BaseModel):
    token: str
    resolution: int
    history: t.List[CoinHistoryDataPoint]

#
# Find price by coin (historical)
# - Allow SigUSD/RSV ergo tokens to be listed as coins (TODO: change from ergo.watch api)
# - Allow multiple coins per blockchain (TODO: change from CoinGecko api)
#
# - Currently Supports
# - all, Ergo, sigUSD, sigRSV, ergopad, Erdoge, Lunadog
# - minimum resolution is 5 mins
@r.get("/price/history/{coin}", response_model=t.List[CoinHistory], name="coin:coin-price-historical")
async def get_asset_historical_price(coin: str = "all", stepSize: int = 1, stepUnit: str = "w", limit: int = 100):
    coin = coin.lower()
    # aggregator stores at 5 min resolution
    timeMap = {
        "m": 1,
        "h": 10,
        "d": 288,
        "w": 2016,
    }
    try:
        # return every nth row
        resolution = int(stepSize * timeMap[stepUnit])
        logging.info(f'Fecthing history for resolution: {resolution}')
        table = "ergodex_ERG/ergodexToken_continuous_5m"
        # sql
        sql = f"""
            SELECT timestamp_utc, sigusd, sigrsv, erdoge, lunadog, ergopad, neta 
            FROM (
                SELECT timestamp_utc, sigusd, sigrsv, erdoge, lunadog, ergopad, neta, ROW_NUMBER() OVER (ORDER BY timestamp_utc DESC) AS rownum 
                FROM "{table}"
            ) as t
            WHERE ((t.rownum - 1) %% {resolution}) = 0
            ORDER BY t.timestamp_utc DESC
            LIMIT {limit}
        """
        logging.debug(f'exec sql: {sql}')
        res = con.execute(sql).fetchall()
        result = []
        # filter tokens
        tokens = ("sigusd", "sigrsv", "erdoge", "lunadog", "ergopad", "neta")
        for index, token in enumerate(tokens):
            if (token != coin and coin != "all"):
                continue

            tokenData = {
                "token": token,
                "resolution": resolution,
                "history": [],
            }
            for row in res:
                ergoPrice = row[1]
                tokenPrice = row[index + 1]
                tokenUSD = 0
                if (tokenPrice != 0):
                    tokenUSD = ergoPrice / tokenPrice
                tokenData["history"].append({
                    "timestamp": row[0],
                    "price": tokenUSD,
                })
            result.append(tokenData)

        # ergo
        if coin in ("ergo", "all"):
            tokenData = {
                "token": "ergo",
                "resolution": resolution,
                "history": [],
            }
            for row in res:
                tokenData["history"].append({
                    "timestamp": row[0],
                    "price": row[1],
                })
            result.append(tokenData)

        return result
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Error: {str(e)}')

#
# Find price by trading pair (ergodex)
#
# - Currently Supports
# - 1. ergopad_erg
# - 2. ergopad_sigusd
@r.get("/price/chart/{pair}", response_model=CoinHistory, name="coin:trading-pair-historical")
async def get_asset_historical_price(pair: str = "ergopad_sigusd", stepSize: int = 1, stepUnit: str = "w", limit: int = 100):
    pair = pair.lower()
    # check cache
    cached = cache.get(f"get_api_asset_price_chart_{pair}_{stepSize}_{stepUnit}_{limit}")
    if cached:
        return cached

    if pair not in ("ergopad_erg", "ergopad_sigusd"):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Error: trading pair not supported')
    # aggregator stores at 5 min resolution
    timeMap = {
        "h": 10,
        "d": 288,
        "w": 2016,
        "m": 8064,
    }
    try:
        # return every nth row
        resolution = int(stepSize * timeMap[stepUnit])
        logging.info(f'Fecthing history for resolution: {resolution}')
        table = "ergodex_ERG/ergodexToken_continuous_5m"
        # sql
        sql = f"""
            SELECT timestamp_utc, sigusd, ergopad
            FROM (
                SELECT timestamp_utc, sigusd, ergopad, ROW_NUMBER() OVER (ORDER BY timestamp_utc DESC) AS rownum 
                FROM "{table}"
            ) as t
            WHERE ((t.rownum - 1) %% {resolution}) = 0
            ORDER BY t.timestamp_utc DESC
            LIMIT {limit}
        """
        logging.debug(f'exec sql: {sql}')
        res = con.execute(sql).fetchall()

        tokenData = {
            "token": pair,
            "resolution": resolution,
            "history": [],
        }
        for row in res:
            num = 1
            if pair == "ergopad_sigusd":
                num = row[1]
            tokenPrice = row[2]
            tokenBase = 0
            if (tokenPrice != 0):
                tokenBase = num / tokenPrice
            tokenData["history"].append({
                "timestamp": str(row[0]),
                "price": tokenBase,
            })

        cache.set(f"get_api_asset_price_chart_{pair}_{stepSize}_{stepUnit}_{limit}", tokenData)
        return tokenData

    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Error: {str(e)}')

#endregion ROUTES

#
# All coin balances and tokens for wallet addresses
# . calls /balance/address
#
class Wallets(BaseModel):
    type: str

# balance of all wallets
@r.post("/balance/all", name="asset:all-wallet-balances")
async def get_all_assets(request: Request) -> None:
    
    wallets = await request.json()

    try:
        # Final balance man contain multiple wallets
        assets = {}

        for wallet in wallets:
            assets[wallet] = []

            # ergo
            if wallet == 'ergo':
                for address in wallets[wallet]:
                    try: assets[wallet].append(await get_asset_balance_from_address(address))
                    except: assets[wallet].append("invalid response")

            # ethereum
            if wallet == 'ethereum':
                for address in wallets[wallet]:
                    try:
                        res = requests.get(f'https://api.ethplorer.io/getAddressInfo/{address}?apiKey=freekey')
                        assets[wallet].append({
                            "address": address,
                            "balance": {
                                'ETH': {
                                    'blockchain': 'ethereum',
                                    'balance': res.json()['ETH']['balance'],
                                    'unconfirmed': 0,
                                    'tokens': None,
                                    'price': (await get_asset_current_price(wallet))['price']
                                }                     
                            }
                        })
                    except: assets[wallet].append("invalid response")

    except Exception as e:
        logging.error(e)

    return assets
