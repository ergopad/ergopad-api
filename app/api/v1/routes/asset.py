import inspect
import logging
import requests
import typing as t

from sqlalchemy import create_engine, text
from wallet import Wallet
from starlette.responses import JSONResponse
from fastapi import APIRouter, status
from fastapi import Path
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.sql.schema import BLANK_SCHEMA
from time import time
from datetime import datetime
from ergodex.price import getErgodexTokenPrice, getErgodexTokenPriceByTokenId
from config import Config, Network  # api specific config
from cache.cache import cache
from db.session import engDanaides

CFG = Config[Network]

asset_router = r = APIRouter()

# region INIT
DEBUG = CFG.debug
st = time()  # stopwatch

currency = 'usd'  # TODO: store with user
total_sigrsv = 100000000000.01  # initial amount SigRSV
default_rsv_price = 1000000  # lower bound/default SigRSV value
nerg2erg = 1000000000.0  # 1e9 satoshis/kushtis in 1 erg
ergo_watch_api = CFG.ergoWatch
oracle_pool_url = CFG.oraclePool
coingecko_url = CFG.coinGecko
exchange = 'coinex'
symbol = 'ERG/USDT'

con = create_engine(CFG.connectionString)
# endregion INIT

# region LOGGING
level = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=level)


def myself(): return inspect.stack()[1][3]
# endregion LOGGING

class AddressList(BaseModel):
    addresses: t.List[str]

# region ROUTES

# Single coin balance and tokens for wallet address
@r.post("/balances/", name="asset:balances")
async def get_assets_for_addresses(req: AddressList):
    try:
        total = 0
        balances = {
            'addresses': {}
        }
        # avoid sql injection by validating wallets
        all_addresses = []
        for address in req.addresses:
            wallet = Wallet(address)
            if wallet.isValid():
                all_addresses.append(address)
            else:
                logging.warning(f'''invalid address '{address}'; potential sql injection''')

        addresses = "','".join([a for a in all_addresses])
        sql = f'''
            select sum(nergs) as nergs, address
            from utxos
            where address in ('{addresses}')
            group by address
        '''
        # logging.debug(sql)
        with engDanaides.begin() as con:
            res = con.execute(sql).fetchall()
        for r in res:
            balances['addresses'][r['address']] = { 'balance': r['nergs']/(10**9), 'tokens': [] }
            total += r['nergs']

        sql = f'''
            select a.address
                , a.token_id
                , a.amount
                , t.token_name
                , coalesce(t.decimals, 0) as decimals
                , coalesce(t.token_type, '') as token_type
                , coalesce(t.token_price, 0.0) as token_price
            from assets a
                left join tokens t on t.token_id = a.token_id
            where a.address in ('{addresses}')
        '''

        logging.debug(sql)
        with engDanaides.begin() as con:
            res = con.execute(sql).fetchall()

        for r in res:
            balances['addresses'][r['address']]['tokens'].append({
                'tokenId': r['token_id'],
                'amount': r['amount'],
                'decimals': r['decimals'],
                'name': r['token_name'],
                'tokenType': r['token_type'],
                'price': r['token_price'],
            })

        balances['total'] = total/(10**9)
        ergo = await get_asset_current_price(coin='ergo')
        balances['price'] = ergo['price']

        return balances

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find balances ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find balances.')

# Single coin balance and tokens for wallet address
@r.get("/balance/{address}", name="asset:wallet-balance")
async def get_asset_balance_from_address(address: str = Path(..., min_length=40, regex="^[a-zA-Z0-9_-]+$")) -> None:
    try:
        addressList = AddressList
        addressList.addresses = [f'{address}']
        return await get_assets_for_addresses(addressList)

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find balance ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find balance ({e})')

# Find price by token_id
# Base currency is USD for all coins and tokens.
@r.get("/priceByTokenId/{tokenId}", name="coin:coin-price-by-token-id")
async def get_ergodex_asset_price_by_token_id(tokenId: str = None):
    try:
        sql = text(f'''
            select token_price 
            from tokens 
            where token_id = :tokenId
        ''')
        price = None
        with engDanaides.begin() as con:
            res = con.execute(sql, {'tokenId': tokenId}).fetchone()
            if res:
                price = res['token_price']
            else:
                price = 0.0

        ret = {
            "status": "unavailable",
            "tokenId": tokenId,
            "price": price
        }

        # set cache only on success
        if price:
            ret["status"] = "ok"
        
        return ret

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find price ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find price ({e})')


# Find price by coin
# Base currency is USD for all coins and tokens.
# - Allow SigUSD/RSV ergo tokens to be listed as coins (TODO: change from ergo.watch api)
# - Allow multiple coins per blockchain (TODO: change from CoinGecko api)
@r.get("/price/{coin}", name="coin:coin-price")
async def get_asset_current_price(coin: str = None):
    try:
        coin = coin.lower()
        # check cache
        cached = cache.get(f"get_api_asset_price_{coin}")
        if cached:
            return cached

        # init/default
        price = None

        # SigUSD/SigRSV
        if coin in ("sigusd", "sigrsv"):
            res = requests.get(ergo_watch_api).json()
            if res:
                if coin == "sigusd":
                    try:
                        # peg_rate_nano: current USD/ERG price [nanoERG]
                        # ERG/USD
                        ergo_price = (await get_asset_current_price("ergo"))["price"]
                        price = (res["peg_rate_nano"] / nerg2erg) * ergo_price  # SIGUSD
                    except:
                        # if get_asset_current_price("ergo") fails
                        price = 1.0
                else:
                    # calc for sigrsv
                    # circ_sigusd: circulating SigUSD tokens in cents
                    circ_sigusd = res["circ_sigusd"] / 100.0
                    # peg_rate_nano: current USD/ERG price [nanoERG]
                    peg_rate_nano = res["peg_rate_nano"]
                    # reserves: total amt in reserves [nanoERG]
                    reserves = res["reserves"]
                    # liabilities in nanoERG's to cover stable coins in circulation
                    # lower of reserves or SigUSD * SigUSD_in_circulation
                    liabilities = min(circ_sigusd * peg_rate_nano, reserves)
                    # find equity, at least 0
                    equity = reserves - liabilities
                    if equity < 0:
                        equity = 0
                    if res["circ_sigrsv"] <= 1:
                        price = 0
                    else:
                        price = (
                            equity / res["circ_sigrsv"]
                        ) / peg_rate_nano  # SigRSV/USD
        # ...all other prices
        else:
            # first check ergodex
            logging.warning("find price from ergodex")
            ret = getErgodexTokenPrice(coin)
            if ret["status"] == "success":
                price = ret["price"]
            else:
                logging.warning(f"invalid ergodex price: {ret}")

            # check local database storage for price
            if price == None:
                logging.warning("find price from aggregator...")
                sqlFindLatestPrice = ''
                try:
                    pairMapper = {
                        "ergo": "ERG/USDT",
                        "erg": "ERG/USDT",
                        "bitcoin": "BTC/USDT",
                        "btc": "BTC/USDT",
                        "ethereum": "ETH/USDT",
                        "eth": "ETH/USDT",
                    }
                    sqlFindLatestPrice = f"""
                        select close 
                        from "{exchange}_{pairMapper[coin]}_1m" 
                        where timestamp_utc > (now() - INTERVAL '5 minutes')
                        order by timestamp_utc 
                        desc limit 1
                    """
                    res = con.execute(sqlFindLatestPrice)
                    price = res.fetchone()[0]
                
                except Exception as e:
                    logging.warning(
                        f"invalid price scraper price: {str(e)}"
                    )

            # if not in local database, ask for online value
            if price == None:
                logging.warning("fallback to price from exchange")
                try:
                    res = requests.get(
                        f"{coingecko_url}/simple/price?vs_currencies={currency}&ids={coin}"
                    )
                    price = res.json()[coin][currency]
                except Exception as e:
                    logging.warning(f"invalid coingecko price: {str(e)}")

        # return value
        ret = {"status": "unavailable", "name": coin, "price": price}

        # do not cache if the api call failed
        if price:
            ret["status"] = "ok"
            cache.set(f"get_api_asset_price_{coin}", ret)

        return ret

    except Exception as e:
        logging.error(f"ERR:{myself()}: unable to find price ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: unable to find price ({e})",
        )


# TokenListRequest
class TokenListRequest(BaseModel):
    tokens: t.List[str]

# Token Price Response Model
class TokenPrice(BaseModel):
    name: str
    price: t.Optional[float]

# Find price for a list of tokens/coins
@r.post("/prices", response_model=t.List[TokenPrice], name="coin:coin-prices")
async def get_asset_current_prices(tokens: TokenListRequest):
    prices = []
    for token in tokens.tokens:
        prices.append({
            "name": token,
            "price": (await get_asset_current_price(token))["price"]
        })
    return prices


# Coin history response schema
class CoinHistoryDataPoint(BaseModel):
    timestamp: datetime
    price: float


class CoinHistory(BaseModel):
    token: str
    resolution: int
    history: t.List[CoinHistoryDataPoint]

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
        logging.error(f'ERR:{myself()}: unable to find historical price ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find historical price ({e})')


# Find price by trading pair (ergodex)
#
# - Currently Supports
# - 1. ergopad_erg
# - 2. ergopad_sigusd
@r.get("/price/chart/{pair}", response_model=CoinHistory, name="coin:trading-pair-historical")
async def get_asset_chart_price(pair: str = "ergopad_sigusd", stepSize: int = 1, stepUnit: str = "w", limit: int = 100):
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

        cache.set(
            f"get_api_asset_price_chart_{pair}_{stepSize}_{stepUnit}_{limit}", tokenData)
        return tokenData

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find price chart ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find price chart ({e})')

# endregion ROUTES

#
# All coin balances and tokens for wallet addresses
# . calls /balance/address
#
class Wallets(BaseModel):
    type: str
