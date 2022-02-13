import requests

"""
========================
File: ergodex/price.py
========================

Implementation  - Python port for @ergolabs/ergodex-sdk-js 
Calculates token price from ergodex liquidity pairs (contract).

Created Date: Jan 23, 2022
"""

# CONSTANTS
API = "https://api.ergoplatform.com/api"
POOL_SAMPLE = "1999030f0400040204020404040405feffffffffffffffff0105feffffffffffffffff01050004d00f040004000406050005000580dac409d819d601b2a5730000d602e4c6a70404d603db63087201d604db6308a7d605b27203730100d606b27204730200d607b27203730300d608b27204730400d6099973058c720602d60a999973068c7205027209d60bc17201d60cc1a7d60d99720b720cd60e91720d7307d60f8c720802d6107e720f06d6117e720d06d612998c720702720fd6137e720c06d6147308d6157e721206d6167e720a06d6177e720906d6189c72117217d6199c72157217d1ededededededed93c27201c2a793e4c672010404720293b27203730900b27204730a00938c7205018c720601938c7207018c72080193b17203730b9593720a730c95720e929c9c721072117e7202069c7ef07212069a9c72137e7214067e9c720d7e72020506929c9c721372157e7202069c7ef0720d069a9c72107e7214067e9c72127e7202050695ed720e917212730d907216a19d721872139d72197210ed9272189c721672139272199c7216721091720b730e"
EMISSION_LP = 9223372036854775807

# ERGO DETAILS
NATIVE_ASSET_ID = '0000000000000000000000000000000000000000000000000000000000000000'
NATIVE_ASSET_TICKER = 'ERG'
NATIVE_ASSET_DECIMALS = 9
NATIVE_ASSET_INFO = {
    "id": NATIVE_ASSET_ID,
    "name": NATIVE_ASSET_TICKER,
    "decimals": NATIVE_ASSET_DECIMALS,
}

# MODELS START


class Asset:
    # Asset Model
    def __init__(self, id, name, decimals):
        self.id = id
        self.name = name
        self.decimals = decimals


class AssetAmount:
    # Asset Amount model
    def __init__(self, asset: Asset, amount: int):
        self.asset = asset
        self.amount = amount

    @staticmethod
    def fromToken(token: dict):
        return AssetAmount(Asset(token["tokenId"], token["name"], token["decimals"]), token["amount"])

    @staticmethod
    def native(amount: int):
        return AssetAmount(Asset(NATIVE_ASSET_INFO["id"], NATIVE_ASSET_INFO["name"], NATIVE_ASSET_INFO["decimals"]), amount)


class Price:
    # asset price y / x
    # note: decimals are not adjusted
    def __init__(self, y: int, x: int):
        self.numerator = y
        self.denominator = x


class AmmPool:
    # Automated Market Maker model
    def __init__(self, id: str, lp: AssetAmount, x: AssetAmount, y: AssetAmount):
        self.id = id
        self.lp = lp
        self.x = x
        self.y = y

    def supplyLP(self) -> int:
        return EMISSION_LP - self.lp.amount

    def getAssetX(self) -> Asset:
        return self.x.asset

    def getAssetY(self) -> Asset:
        return self.y.asset

    def getPriceY(self) -> Price:
        return Price(self.y.amount, self.x.amount)

    def getPriceX(self) -> Price:
        return Price(self.x.amount, self.y.amount)

    def getCalculatedPrice(self) -> dict:
        # return calculated price
        # tokens / erg
        decimalX = 10 ** self.x.asset.decimals
        decimalY = 10 ** self.y.asset.decimals
        price = ((self.y.amount * decimalX) / (self.x.amount * decimalY))
        return {
            "assetX": self.x.asset.name,
            "assetY": self.y.asset.name,
            "price": round(price, self.y.asset.decimals),
        }


def parseRegisterId(key):
    if key in ('R4', 'R5', 'R6', 'R7', 'R8', 'R9'):
        return key
    return None


def explorerToErgoBox(box):
    registers = {}
    for key in box["additionalRegisters"]:
        regId = parseRegisterId(key)
        if (regId):
            registers[regId] = box["additionalRegisters"][key]["serializedValue"]

    return {
        "boxId": box["boxId"],
        "index": box["index"],
        "value": box["value"],
        "assets": box["assets"],
        "additionalRegisters": registers
    }


def parsePool(box) -> AmmPool:
    if len(box["assets"]) == 3 and "R4" in box["additionalRegisters"]:
        nft = box["assets"][0]["tokenId"]
        lp = AssetAmount.fromToken(box["assets"][1])
        assetX = AssetAmount.native(box["value"])
        assetY = AssetAmount.fromToken(box["assets"][2])
        return AmmPool(nft, lp, assetX, assetY)
    return None


def parseValidPools(boxes) -> list[AmmPool]:
    pools: list[AmmPool] = []
    for box in boxes:
        pool = parsePool(box)
        if pool:
            pools.append(pool)

    # check for collisions
    filter = {}
    for pool in pools:
        uid = pool.getAssetX().id + "-" + pool.getAssetY().id
        if uid not in filter:
            filter[uid] = pool
        else:
            # consider pool with higher liquidity
            if filter[uid].x.amount < pool.x.amount:
                filter[uid] = pool

    filteredPools = [filter[uid] for uid in filter]
    return filteredPools


def getTokenPrice(token, prices):
    # return price of token from prices
    for price in prices:
        if price["assetY"].lower() == token.lower():
            return price["price"]
    return None


# main export
def getErgodexTokenPrice(tokenName: str):
    tokenName = tokenName.lower()
    try:
        res = requests.get(f'{API}/v1/boxes/unspent/byErgoTree/{POOL_SAMPLE}/')
        boxes = list(map(explorerToErgoBox, res.json()["items"]))
        pools = parseValidPools(boxes)
        prices = [pool.getCalculatedPrice() for pool in pools]
        SigUSD_ERG = getTokenPrice("SigUSD", prices)
        token_ERG = getTokenPrice(tokenName, prices)
        SigUSD_token = SigUSD_ERG / token_ERG
        return {
            "name": tokenName,
            "price": SigUSD_token,
            "status": "success"
        }
    except:
        return {
            "name": tokenName,
            "price": 0.0,
            "status": "error"
        }


if __name__ == "__main__":
    res = requests.get(f'{API}/v1/boxes/unspent/byErgoTree/{POOL_SAMPLE}/')
    boxes = list(map(explorerToErgoBox, res.json()["items"]))
    pools = parseValidPools(boxes)
    for pool in pools:
        print(pool.getCalculatedPrice())
