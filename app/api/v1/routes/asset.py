from enum import Enum
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
from datetime import datetime, date, timedelta
from ergodex.price import getErgodexTokenPrice, getErgodexTokenPriceByTokenId
from config import Config, Network  # api specific config
from cache.cache import cache
from db.session import engDanaides
from ergo_python_appkit.appkit import ErgoAppKit
from org.ergoplatform.appkit import ErgoValue, NetworkType
from org.ergoplatform import ErgoAddressEncoder
from sigmastate.serialization import ErgoTreeSerializer

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
def get_assets_for_addresses(req: AddressList):
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
        ergo = get_asset_current_price(coin='ergo')
        balances['price'] = ergo['price']

        return balances

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find balances ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find balances.')

# Single coin balance and tokens for wallet address
@r.get("/balance/{address}", name="asset:wallet-balance")
def get_asset_balance_from_address(address: str = Path(..., min_length=40, regex="^[a-zA-Z0-9_-]+$")) -> None:
    try:
        addressList = AddressList
        addressList.addresses = [f'{address}']
        return get_assets_for_addresses(addressList)

    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find balance ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find balance ({e})')

# Find price by token_id
# Base currency is USD for all coins and tokens.
@r.get("/priceByTokenId/{tokenId}", name="coin:coin-price-by-token-id")
def get_ergodex_asset_price_by_token_id(tokenId: str = None):
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
def get_asset_current_price(coin: str = None):
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
                        ergo_price = (get_asset_current_price("ergo"))["price"]
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
def get_asset_current_prices(tokens: TokenListRequest):
    prices = []
    for token in tokens.tokens:
        prices.append({
            "name": token,
            "price": (get_asset_current_price(token))["price"]
        })
    return prices

class TokenType(Enum):
    PICTURE = "0e020101"
    AUDIO = "0e020102"
    VIDEO = "0e020103"
    COLLECTION = "0e020104"
    PACK = "0e020105"
    OTHER = ""

    @classmethod
    def _missing_(cls, value):
        return cls.OTHER
    
def isP2PK(addr: str):
    return len(addr) == 51 and addr[0] == "9"
    
@r.get("/info/{tokenId}/minter", name="token:minter")
def get_token_minter(tokenId: str):
    try:
        cached = cache.get(f"get_token_minter_{tokenId}")
        if cached:
            return cached
        res = requests.get(CFG.node+"/blockchain/box/byId/"+tokenId)
        tokenIds = [tokenId]
        if res.ok:
            issuerBox = res.json()
            if isP2PK(issuerBox["address"]):
                result = {"minterAddress": issuerBox["address"]}
            else:
                res = requests.get(CFG.node+"/blockchain/transaction/byId/"+issuerBox['transactionId'])
                if res.ok:
                    minterAddress = ""
                    findMinterTransaction = res.json()
                    cached = cache.get(f"get_token_minter_{findMinterTransaction['inputs'][0]['boxId']}")
                    if cached:
                        minterAddress = cached["minterAddress"]
                    while minterAddress == "":
                        if isP2PK(findMinterTransaction["inputs"][0]["address"]):
                            minterAddress = findMinterTransaction["inputs"][0]["address"]
                        else:
                            tokenIds.append(findMinterTransaction["inputs"][0]["boxId"])
                            res = requests.get(CFG.node+"/blockchain/transaction/byId/"+findMinterTransaction["inputs"][0]['transactionId'])
                            if res.ok:
                                findMinterTransaction = res.json()
                    result = {
                        "minterAddress": minterAddress
                    }
        for tok in tokenIds:    
            cache.set(f"get_token_minter_{tok}", result, 3600)
        return result
    except Exception as e:
        logging.error(e)
        return e

@r.get("/info/{tokenId}", name="token:info")
def get_token_info(tokenId: str):
    try:
        cached = cache.get(f"get_token_info_{tokenId}")
        if cached:
            return cached
        res = requests.get(CFG.node+"/blockchain/box/byId/"+tokenId)
        if res.ok:
            issuerBox = res.json()
            res = requests.get(CFG.node+"/blockchain/transaction/byId/"+issuerBox['spentTransactionId'])
            if res.ok:
                mintTransaction = res.json()
                issuanceBox = None
                for output in mintTransaction['outputs']:
                    if output['assets'][0]['tokenId'] == tokenId:
                        issuanceBox = output
                        break
                tokenName = bytes(ErgoValue.fromHex(issuanceBox["additionalRegisters"]["R4"]).getValue().toArray()).decode("utf-8")
                tokenDescription = bytes(ErgoValue.fromHex(issuanceBox["additionalRegisters"]["R5"]).getValue().toArray()).decode("utf-8")
                try:
                    tokenDecimals = int(bytes(ErgoValue.fromHex(issuanceBox["additionalRegisters"]["R6"]).getValue().toArray()).decode("utf-8"))
                except:
                    tokenDecimals = 0
                totalMinted = issuanceBox['assets'][0]['amount']

                if "R7" in issuanceBox["additionalRegisters"]:
                    nftType = TokenType(issuanceBox["additionalRegisters"]["R7"])
                else:
                    nftType = TokenType.OTHER

                extraMetaData = {}

                if nftType == TokenType.COLLECTION:
                    collectionStandard = int(ErgoValue.fromHex(issuerBox["additionalRegisters"]["R4"]).getValue())
                    collectionInfo = ErgoValue.fromHex(issuerBox["additionalRegisters"]["R5"]).getValue().toArray()
                    collectionLogo = bytes(collectionInfo[0].toArray()).decode("utf-8")
                    collectionFeaturedImage = bytes(collectionInfo[1].toArray()).decode("utf-8")
                    collectionBannerImage = bytes(collectionInfo[2].toArray()).decode("utf-8")
                    collectionCategory = bytes(collectionInfo[3].toArray()).decode("utf-8")

                    collectionSocials = ErgoValue.fromHex(issuerBox["additionalRegisters"]["R6"]).getValue().toArray()
                    socials = []
                    for soc in collectionSocials:
                        socials.append({
                            "platform": bytes(soc._1().toArray()).decode("utf-8"), "link": bytes(soc._2().toArray()).decode("utf-8")
                        })
                    try:
                        mintingExpiry = int(ErgoValue.fromHex(issuerBox["additionalRegisters"]["R7"]).getValue())
                    except:
                        mintingExpiry = -1

                    additionalInfo = []
                    try:
                        collectionAdditionalInfo = ErgoValue.fromHex(issuerBox["additionalRegisters"]["R8"]).getValue().toArray()
                        for inf in collectionAdditionalInfo:
                            additionalInfo.append({
                                bytes(inf._1().toArray()).decode("utf-8"): bytes(inf._2().toArray()).decode("utf-8")
                            })
                    except:
                        additionalInfo = []

                    extraMetaData = {
                        "standard": collectionStandard,
                        "logo": collectionLogo,
                        "featuredImage": collectionFeaturedImage,
                        "bannerImage": collectionBannerImage,
                        "category": collectionCategory,
                        "socials": socials,
                        "mintingExpiry": mintingExpiry,
                        "additionalInfo": additionalInfo
                    }

                if nftType == TokenType.PICTURE or nftType == TokenType.PACK:
                    pictureHash = bytes(ErgoValue.fromHex(issuanceBox["additionalRegisters"]["R8"]).getValue().toArray()).hex()
                    pictureLink = bytes(ErgoValue.fromHex(issuanceBox["additionalRegisters"]["R9"]).getValue().toArray()).decode("utf-8")
                    artworkStandard = 0
                    royalty = []
                    if "additionalRegisters" in issuerBox:
                        if "R4" in issuerBox["additionalRegisters"]:
                            artworkStandard = int(ErgoValue.fromHex(issuerBox["additionalRegisters"]["R4"]).getValue())
                            if artworkStandard > 10:
                                royalty.append({"address": get_token_minter(tokenId)["minterAddress"], "royaltyPct": artworkStandard/10})
                                artworkStandard = 1
                    standard2Data = {}
                    if artworkStandard == 2:
                        royalties = ErgoValue.fromHex(issuerBox["additionalRegisters"]["R5"]).getValue().toArray()
                        for roy in royalties:
                            royalty.append({"address": ErgoAddressEncoder(NetworkType.MAINNET.networkPrefix).fromProposition(ErgoTreeSerializer().deserializeErgoTree(roy._1().toArray())).get().toString(),
                                            "royaltyPct": int(roy._2())/10})
                            
                        traits = {}
                        artworkTraits = ErgoValue.fromHex(issuerBox["additionalRegisters"]["R6"]).getValue()
                        properties = []
                        for prop in artworkTraits._1().toArray():
                            properties.append({"name": bytes(prop._1().toArray()).decode("utf-8"), "value": bytes(prop._2().toArray()).decode("utf-8")})
                        traits["properties"] = properties
                        levels = []
                        for lev in artworkTraits._2()._1().toArray():
                            levels.append({"name": bytes(lev._1().toArray()).decode("utf-8"), "value": int(lev._2()._1()), "max": int(lev._2()._2())})
                        traits["levels"] = levels
                        stats = []
                        for stat in artworkTraits._2()._2().toArray():
                            stats.append({"name": bytes(stat._1().toArray()).decode("utf-8"), "value": int(stat._2()._1()), "max": int(stat._2()._2())})
                        traits["stats"] = stats
                        standard2Data["traits"] = traits

                        collection = {}
                        collectionId = bytes(ErgoValue.fromHex(issuerBox["additionalRegisters"]["R7"]).getValue().toArray()).hex()
                        if len(collectionId) > 0:
                            foundCollectionToken = False
                            for ass in issuerBox["assets"]:
                                if ass["tokenId"] == collectionId:
                                    foundCollectionToken = True
                            if foundCollectionToken:
                                collection = get_token_info(collectionId)
                                if collection["nftType"] != "COLLECTION":
                                    collection = {}
                        standard2Data["collection"] = collection
                        additionalInfo = []
                        if "R8" in issuerBox["additionalRegisters"]:
                            additionalInfos = ErgoValue.fromHex(issuerBox["additionalRegisters"]["R8"]).getValue().toArray()
                            for ai in additionalInfos:
                                additionalInfo.append({"key": bytes(ai._1().toArray()).decode("utf-8"), "value": bytes(ai._2().toArray()).decode("utf-8")})
                        standard2Data["additionalInfo"] = additionalInfo
                        

                    extraMetaData = {
                        "hash": pictureHash,
                        "link": pictureLink,
                        "standard": artworkStandard,
                        "royalty": royalty,
                        "standard2Data": standard2Data
                    }

                    result = {
                        "name": tokenName,
                        "description": tokenDescription,
                        "decimals": tokenDecimals,
                        "totalMinted": totalMinted,
                        "nftType": nftType.name,
                        "extraMetaData": extraMetaData
                    }

                    cache.set(f"get_token_info_{tokenId}", result, 3600)

                return {
                    "name": tokenName,
                    "description": tokenDescription,
                    "decimals": tokenDecimals,
                    "totalMinted": totalMinted,
                    "nftType": nftType.name,
                    "extraMetaData": extraMetaData
                }
    except Exception as e:
        logging.error(e)
        return e



# Coin history response schema
class CoinHistoryDataPoint(BaseModel):
    timestamp: datetime
    price: float


class CoinHistory(BaseModel):
    token: str
    resolution: str
    history: t.List[CoinHistoryDataPoint]

# Find price by coin (historical)
# - Allow SigUSD/RSV ergo tokens to be listed as coins (TODO: change from ergo.watch api)
# - Allow multiple coins per blockchain (TODO: change from CoinGecko api)
#
# - Currently Supports
# - all, Ergo, sigUSD, sigRSV, ergopad, Erdoge, Lunadog
# - minimum resolution is 5 mins
@r.get("/price/history/{coin}", response_model=t.List[CoinHistory], name="coin:coin-price-historical")
def get_asset_historical_price(coin: str = "all", stepSize: int = 1, stepUnit: str = "w", limit: int = 100, base: str = "sigusd"):
    coin = coin.lower()

    if base not in ("erg","sigusd"):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Error: base {base} not supported')

    try:

        interval = f"{stepSize} {stepUnit}"
        from_date = date.today() - timedelta(
            weeks = (stepSize*limit if stepUnit=="w" else 0),
            days = (stepSize*limit if stepUnit=="d" else 0), 
            hours = (stepSize*limit if stepUnit=="h" else 0),
            minutes = (stepSize*limit if stepUnit=="m" else 0))
        to_date = date.today() + timedelta(days = 1)

        # return every nth row
        
        result = []
        # filter tokens
        tokens = ("sigrsv", "ergopad", "neta", "paideia", "egio", "exle", "terahertz", "epos", "aht", "cypx")
        for token in tokens:
            if (token != coin and coin != "all"):
                continue

            cached = cache.get(f"get_api_asset_price_history_{token}_{base}_{stepSize}_{stepUnit}_{limit}")
            if cached:
                result.append(cached)
            else:
                sql = f"""
                    WITH token_pool_id as (
                        SELECT "poolId" 
                        FROM pool_tvl_mat 
                        WHERE lower("tokenName") = %(token)s
                        ORDER BY "value" DESC
                        LIMIT 1
                    ), sigusd_pool_id as (
                        SELECT "poolId" 
                        FROM pool_tvl_mat 
                        WHERE lower("tokenName") = 'sigusd'
                        ORDER BY "value" DESC
                        LIMIT 1
                    )
                    SELECT token_history."time", token_history."close" as token_price, ergo_history."close" as ergo_price
                    FROM getohlcv((SELECT "poolId" FROM token_pool_id),interval %(interval)s, to_timestamp(%(from_date)s,'YYYY-MM-DD'),to_timestamp(%(to_date)s,'YYYY-MM-DD'), false) as token_history
                    INNER JOIN getohlcv((SELECT "poolId" FROM sigusd_pool_id),interval %(interval)s, to_timestamp(%(from_date)s,'YYYY-MM-DD'),to_timestamp(%(to_date)s,'YYYY-MM-DD'), false) as ergo_history
                    ON token_history."time" = ergo_history."time"
                    ORDER BY token_history."time" DESC
                    LIMIT %(limit)s
                """ if base == "sigusd" else f"""
                    WITH token_pool_id as (
                        SELECT "poolId" 
                        FROM pool_tvl_mat 
                        WHERE lower("tokenName") = %(token)s
                        ORDER BY "value" DESC
                        LIMIT 1
                    )
                    SELECT token_history."time", token_history."close" as token_price
                    FROM getohlcv((SELECT "poolId" FROM token_pool_id),interval %(interval)s, to_timestamp(%(from_date)s,'YYYY-MM-DD'),to_timestamp(%(to_date)s,'YYYY-MM-DD'), true) as token_history
                    ORDER BY token_history."time" DESC
                    LIMIT %(limit)s
                """

                res = con.execute(sql,{"token": token, "interval": interval, "from_date": str(from_date), "to_date": str(to_date), "limit": limit}).fetchall()
                res.reverse()
                tokenData = {
                    "token": token,
                    "resolution": interval,
                    "history": [],
                }
                ergoPrice = 1
                tokenPrice = 0
                for row in res:
                    if base == "sigusd":
                        ergoPrice = row[2] if row[2] is not None else ergoPrice
                        tokenPrice = row[1] if row[1] is not None else tokenPrice
                        tokenUSD = 0
                        if (tokenPrice != 0):
                            tokenUSD = ergoPrice / tokenPrice
                    else:
                        tokenUSD = row[1] if row[1] is not None else 0
                    tokenData["history"].append({
                        "timestamp": row[0],
                        "price": tokenUSD,
                    })
                tokenData["history"].reverse()
                result.append(tokenData)
                cache.set(f"get_api_asset_price_history_{token}_{base}_{stepSize}_{stepUnit}_{limit}", tokenData)

        # ergo
        if coin in ("ergo", "all") and base != "erg":
            cached = cache.get(f"get_api_asset_price_history_ergo_{base}_{stepSize}_{stepUnit}_{limit}")
            if cached:
                result.append(cached)
            else:
                sql = f"""
                    WITH sigusd_pool_id as (
                        SELECT "poolId" 
                        FROM pool_tvl_mat 
                        WHERE lower("tokenName") = 'sigusd'
                        ORDER BY "value" DESC
                        LIMIT 1
                    )
                    SELECT ergo_history."close" as ergo_price, ergo_history."time"
                    FROM getohlcv((SELECT "poolId" FROM sigusd_pool_id),interval %(interval)s, to_timestamp(%(from_date)s,'YYYY-MM-DD'),to_timestamp(%(to_date)s,'YYYY-MM-DD'), false) as ergo_history
                    ORDER BY ergo_history."time" DESC
                    LIMIT %(limit)s
                """

                res = con.execute(sql,{"interval": interval, "from_date": str(from_date), "to_date": str(to_date), "limit": limit}).fetchall()

                tokenData = {
                    "token": "ergo",
                    "resolution": interval,
                    "history": [],
                }
                for row in res:
                    if row[0] is not None:
                        tokenData["history"].append({
                            "timestamp": row[1],
                            "price": row[0],
                        })
                result.append(tokenData)
                cache.set(f"get_api_asset_price_history_ergo_{base}_{stepSize}_{stepUnit}_{limit}", tokenData)

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
def get_asset_chart_price(pair: str = "ergopad_sigusd", stepSize: int = 1, stepUnit: str = "w", limit: int = 100):
    pair = pair.lower()

    if pair not in ("ergopad_erg", "ergopad_sigusd"):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Error: trading pair not supported')
        
    pairSplit = pair.split('_')
    result = get_asset_historical_price(pairSplit[0],stepSize,stepUnit,limit,pairSplit[1])

    if len(result) > 0:
        return result[0]
    else:
        return "No chart data found"

@r.get("/price/{token}/{timestamp}", name="coin:price-point-in-time")
def get_asset_price_at_time(token: str, timestamp: int):
    token = token.lower()
    sql = f"""
            WITH token_pool_id as (
                SELECT "poolId" 
                FROM pool_tvl_mat 
                WHERE lower("tokenName") = %(token)s
                ORDER BY "value" DESC
                LIMIT 1
            )
            SELECT ("value"/10^9)/("tokenAmount"/10^"tokenDecimals")
            FROM spectrum_boxes
			where "poolId" = (select "poolId" from token_pool_id)
			and global_index = (select max(global_index) from spectrum_boxes where "poolId" = (select "poolId" from token_pool_id) and "timestamp" < to_timestamp(%(timestamp)s))
            """

    res = con.execute(sql,{"token": token, "timestamp": timestamp}).fetchone()
    if res:
        return {"price":res[0]}
    else:
        return {"price": 0}

            

class OHLCVData(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    time: datetime

@r.get("/ohlcv/{token}/{base}/{barSize}/{barSizeUnit}/{fromDate}/{toDate}", response_model=t.List[OHLCVData], name="token:base-ohlcv")
def get_asset_ohlcv_data(token: str, base: str, barSize: int, barSizeUnit: str, fromDate: date, toDate: date, offset: int = 0, limit: int = 500):
    try:
        ergSigUsd = None
        if token == "sigusd" and base != "erg":
            ergSigUsd = get_asset_ohlcv_data("erg", "sigusd", barSize, barSizeUnit, fromDate, toDate, offset, limit)
            token = "erg"
        if limit > 500 or limit < 1:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: limit should be a value between 1 and 500')
        if barSizeUnit not in ("h","d","w"):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: barSizeUnit needs to be h, d or w')
        if base not in ("erg") and token not in ("erg"):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: base or token needs to be erg')
        result = []
        cached = cache.get(f"get_asset_ohlcv_data_{token}_{base}_{barSize}_{barSizeUnit}")
        if not cached:
            cached = cache.get(f"get_asset_ohlcv_data_{token}_{base}_{barSize}_{barSizeUnit}_long")
            if not cached:
                cached = {}
                refreshCacheDate = str(date(2021,8,1))
            else:
                refreshCacheDate = list(cached.keys())[-1]
                cached[refreshCacheDate] = []

            interval = f"{barSize} {barSizeUnit}"

            sql = f"""
            WITH token_pool_id as (
                SELECT "poolId" 
                FROM pool_tvl_mat 
                WHERE lower("tokenName") = %(token)s
                ORDER BY "value" DESC
                LIMIT 1
            )
            SELECT "open", "high", "low", "close", "volume", "time"
            FROM getohlcv((SELECT "poolId" FROM token_pool_id),interval %(interval)s, to_timestamp(%(from_date)s,'YYYY-MM-DD'),to_timestamp(%(to_date)s,'YYYY-MM-DD'), %(flipped)s) as token_history
            ORDER BY token_history."time"
            """

            res = con.execute(sql,{"token": (base if token == "erg" else token), "interval": interval, "from_date": str(refreshCacheDate), "to_date": str(date.today()+timedelta(days=1)), "flipped": (token == "erg")}).fetchall()

            for row in res:
                if row[0] is not None:
                    elementDate = str(date.fromtimestamp(row[5]))
                    if elementDate not in cached.keys():
                        cached[elementDate] = []
                    cached[elementDate].append({"open":row[0],"high":row[1],"low":row[2],"close":row[3],"volume":row[4],"time":row[5]})

            cache.set(f"get_asset_ohlcv_data_{token}_{base}_{barSize}_{barSizeUnit}",cached)
            #cache.set(f"get_asset_ohlcv_data_{token}_{base}_{barSize}_{barSizeUnit}_long",cached,3600)

        index = 0
        for ohlcvdate_str in cached.keys():
            ohlcvdate = date.fromisoformat(ohlcvdate_str)
            if ohlcvdate >= fromDate and ohlcvdate <= toDate:
                for data_row in cached[str(ohlcvdate)]:
                    if offset + limit > 0 and offset + limit <= limit and data_row["time"] < datetime.now().timestamp():
                        if ergSigUsd is not None:
                            while ergSigUsd[index]["time"] < data_row["time"]:
                                index += 1
                            if ergSigUsd[index]["time"] == data_row["time"]:
                                avgErgPrice = (ergSigUsd[index]["open"] + ergSigUsd[index]["close"])/2
                                result.append({
                                    "open": data_row["open"]/ergSigUsd[index]["open"], 
                                    "high": data_row["high"]/avgErgPrice,
                                    "low": data_row["low"]/avgErgPrice,
                                    "close": data_row["close"]/ergSigUsd[index]["close"],
                                    "volume": data_row["volume"]/avgErgPrice,
                                    "time": data_row["time"]})
                            index += 1
                        else:
                            result.append(data_row)
                    offset -= 1

        logging.info(result[0])
        return result
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to find ohlcv data ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: unable to find ohlcv data ({e})')

# endregion ROUTES

#
# All coin balances and tokens for wallet addresses
# . calls /balance/address
#
class Wallets(BaseModel):
    type: str
