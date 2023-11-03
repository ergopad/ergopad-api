import requests
from decimal import Decimal

from starlette.responses import JSONResponse
from wallet import Wallet
from config import Config, Network  # api specific config
from fastapi import APIRouter, Request, Depends, Response, encoders, status
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
from time import time
from datetime import datetime
from base64 import b64encode
from ergo.util import encodeLongArray, encodeString, hexstringToB64
from hashlib import blake2b
from api.v1.routes.blockchain import (
    TXFormat,
    getNFTBox,
    getTokenInfo,
    getErgoscript,
    getBoxById,
)
from db.session import get_db
from db.crud.staking_config import (
    get_all_staking_config,
    get_staking_config_by_name,
    create_staking_config,
    edit_staking_config,
    delete_staking_config,
)
from db.schemas.stakingConfig import StakingConfig, CreateAndUpdateStakingConfig
from core.auth import get_current_active_superuser, get_current_active_user
from core.security import get_md5_hash
from db.session import engDanaides
from cache.staking import AsyncSnapshotEngine
from cache.cache import cache

from ergo_python_appkit.appkit import ErgoAppKit, ErgoValueT
from org.ergoplatform.appkit import Address, ErgoValue, OutBox, InputBox

from paideia_contracts.contracts.staking import (
    CreateAddStakeProxyTransaction,
    CreateStakeProxyTransaction,
    CreateUnstakeProxyTransaction,
    NETAConfig,
    PaideiaConfig,
    PaideiaTestConfig,
    EGIOConfig,
    AHTConfig,
    Ergo_Crux_LPConfig,
)

stakingConfigs = {
    "paideiatest": PaideiaTestConfig,
    "paideia": PaideiaConfig,
    "egiov2": EGIOConfig,
    "neta": NETAConfig,
    "aht": AHTConfig,
    "crux": Ergo_Crux_LPConfig,
}

stakingConfigsV1 = {
    "ergopad": {
        "tokenName": "ErgoPad",
        "stakeStateNFT": "05cde13424a7972fbcd0b43fccbb5e501b1f75302175178fc86d8f243f3f3125",
        "stakePoolNFT": "0d01f2f0b3254b4a1731e1b61ad77641fe54de2bd68d1c6fc1ae4e7e9ddfb212",
        "emissionNFT": "0549ea3374a36b7a22a803766af732e61798463c3332c5f6d86c8ab9195eed59",
        "stakeTokenID": "1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee",
        "stakedTokenID": "d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413",
        "stakeAddress": "3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9",
    },
    "egio": {
        "tokenName": "EGIO",
        "stakeStateNFT": "f419099a27aaa5f6f7d109d8773b1862e8d1857b44aa7d86395940d41eb53806",
        "stakePoolNFT": "07a8648d0de0f7c87aad41a1fbc6d393a6ad95584d38c47c88125bef101c29e9",
        "emissionNFT": "a8d633dee705ff90e3181013381455353dac2d91366952209ac6b3f9cdcc23e9",
        "stakeTokenID": "1431964fa6559e969a7bf047405d3f63f7592354d432556f79894a12c4286e81",
        "stakedTokenID": "00b1e236b60b95c2c6f8007a9d89bc460fc9e78f98b09faec9449007b40bccf3",
        "stakeAddress": "3eiC8caSy3jixP2iRTiYygUaYjRXXa45eva19FqeMD24Tykh17yux6MqT4t7FB2kHtFethYZjKhpBQyqSsUWdRWtwz1a8KMNnmEykv5JmT3sA6V6ZNfAtzdV8acRoBXhteVQ8nDMywZ8FvcBVbw6yBvXpcDjXRHzgbb35YHi51xJ9ZooaAmLHqBCJhXVMM1enpUYRxNPXdVZgeGnygmLq6k9LRS7Sp2MKciicyqbWpW8wVnzewmoEkvteCeAHErHkBagdLsYbs9dgBAktqAgwTvTRhLMkC42eWHnenAaFNih4GpReq9tz9AMhDJYWd2n7WVCDnVkDT6CXe8d83jSFkMaoiFoBLGqy5M68jMjUNS2yHuLo1GnyMjukB3y5N1vbyjUFstVPgHCs99e8LGE2QUE5YbX1LBQz934XvZo1heTXVfevmm9bZWBiruiwH7kCcv81tRE2Y22nk6EDMWdyYUYchjK31KqcMRrF2hdWFtocAL3bz3Pniz4zjnrFQQcWMsVypZRzqdWAdKpVjZswP4k4VyBJAerHniekyBQ5FMhtN3kNWUKHXYkhmqSmaiEx2Uw4JiK9KnXapT",
    },
}

staking_router = r = APIRouter()

# region INIT
CFG = Config[Network]
DEBUG = True  # CFG.DEBUG
DATABASE = CFG.connectionString
VERBOSE = CFG.debug

CFG[
    "stakeStateNFT"
] = "05cde13424a7972fbcd0b43fccbb5e501b1f75302175178fc86d8f243f3f3125"
CFG["stakePoolNFT"] = "0d01f2f0b3254b4a1731e1b61ad77641fe54de2bd68d1c6fc1ae4e7e9ddfb212"
CFG["emissionNFT"] = "0549ea3374a36b7a22a803766af732e61798463c3332c5f6d86c8ab9195eed59"
CFG["stakeTokenID"] = "1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee"
CFG[
    "stakedTokenID"
] = "d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413"

nergsPerErg = 10**9
headers = {"Content-Type": "application/json"}

week = 1000 * 60 * 60 * 24 * 7
duration_ms = {
    "month": 365 * 24 * 60 * 60 * 1000 / 12,
    "week": week,
    "day": 24 * 60 * 60 * 1000,
    "minute": 60 * 1000,
}
# endregion INIT

# region LOGGING
import logging

levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format="{asctime}:{name:>8s}:{levelname:<8s}::{message}",
    style="{",
    levelname=levelname,
)

import inspect

myself = lambda: inspect.stack()[1][3]
# endregion LOGGING


# region CLASSES
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
    emissionStart_ms: int


# endregion CLASSES


# TODO: since index is not saved currently with assets in danaides, keep using public explorer for now
@r.post("/unstake/", name="staking:unstake")
def unstake(req: UnstakeRequest, project: str = "ergopad"):
    try:
        logging.debug(f"*****************{req}*****************")
        sc = stakingConfigsV1[project]
        logging.debug("unstake::appKit")
        appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)
        stakedTokenInfo = getTokenInfo(sc["stakedTokenID"])
        logging.debug("unstake::get NFT stakeStateBox")
        stakeStateBox = getNFTBox(sc["stakeStateNFT"])
        if stakeStateBox is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Unable to find stake state box",
            )

        stakeBox = getBoxById(req.stakeBox, isStateBox=True)
        stakeBox["address"] = requests.get(
            f'{CFG.node}/utils/ergoTreeToAddress/{stakeBox["ergoTree"]}'
        ).json()["address"]
        # remaining = int(req.stakeBox["assets"][1]["amount"]) - amountToUnstake
        remaining = 0
        for ass in stakeBox["assets"]:
            # ergopad only
            if (
                ass["tokenId"]
                == "d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413"
            ):
                try:
                    remaining = int(ass["amount"])
                except:
                    remaining = 0

        # logging.debug('unstake::find stakeBox')
        currentTime = int(time() * 1000)
        amountToUnstake = min(
            int(req.amount * 10 ** stakedTokenInfo["decimals"]), remaining
        )

        logging.debug(f"unstake::find remaining=={remaining}")
        if remaining > 0 and remaining < 1000:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Remaining amount needs to be at least 10 ErgoPad",
            )
        stakeBoxR4 = eval(stakeBox["additionalRegisters"]["R4"]["renderedValue"])
        stakeTime = stakeBoxR4[1]

        logging.debug("unstake::get NFG userBox")
        userBox = getNFTBox(stakeBox["additionalRegisters"]["R5"]["renderedValue"])
        timeStaked = currentTime - stakeTime
        weeksStaked = int(timeStaked / week)
        penalty = int(
            0
            if (weeksStaked >= 8)
            else amountToUnstake * 5 / 100
            if (weeksStaked >= 6)
            else amountToUnstake * 125 / 1000
            if (weeksStaked >= 4)
            else amountToUnstake * 20 / 100
            if (weeksStaked >= 2)
            else amountToUnstake * 25 / 100
        )
        partial = amountToUnstake < remaining  # int(stakeBox["assets"][1]["amount"])

        logging.debug("unstake::stake state R4")
        stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
        if stakeStateR4[1] != stakeBoxR4[0]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"This stake box has a pending compound transaction. Compounding needs to happen before unstaking.",
            )

        logging.debug("unstake::build outBox 1")
        # int(stakeStateBox["assets"][1]["amount"])
        stakeStateAmountToUnstake = 0
        for ass in stakeStateBox["assets"]:
            if (
                ass["tokenId"]
                == "1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee"
            ):
                try:
                    stakeStateAmountToUnstake = int(ass["amount"])
                except:
                    stakeStateAmountToUnstake = 0

        if not partial:
            stakeStateAmountToUnstake += 1
        outputs = []
        outputs.append(
            appKit.buildOutBox(
                value=stakeStateBox["value"],
                tokens={
                    sc["stakeStateNFT"]: 1,
                    sc["stakeTokenID"]: stakeStateAmountToUnstake,
                },
                registers=[
                    ErgoAppKit.ergoValue(
                        [
                            int(stakeStateR4[0] - amountToUnstake),
                            int(stakeStateR4[1]),
                            int(stakeStateR4[2] - (0 if (partial) else 1)),
                            int(stakeStateR4[3]),
                            int(stakeStateR4[4]),
                        ],
                        ErgoValueT.LongArray,
                    )
                ],
                contract=appKit.contractFromAddress(stakeStateBox["address"]),
            )
        )

        logging.debug("unstake::build outBox 2")
        outputs.append(
            appKit.buildOutBox(
                value=int(0.01 * nergsPerErg),
                tokens={
                    sc["stakedTokenID"]: amountToUnstake - penalty,
                    stakeBox["additionalRegisters"]["R5"]["renderedValue"]: 1,
                }
                if (partial)
                else {sc["stakedTokenID"]: amountToUnstake - penalty},
                registers=None,
                contract=appKit.contractFromAddress(userBox["address"]),
            )
        )

        try:
            logging.debug(f"unstake::partial=={partial}")
        except:
            pass
        assetsToBurn = {}
        if partial:
            outputs.append(
                appKit.buildOutBox(
                    value=stakeBox["value"],
                    tokens={
                        sc["stakeTokenID"]: 1,
                        sc["stakedTokenID"]: remaining
                        - amountToUnstake,  # stakeBox["assets"][1]["amount"]-amountToUnstake
                    },
                    registers=[
                        ErgoValue.fromHex(
                            stakeBox["additionalRegisters"]["R4"]["serializedValue"]
                        ),
                        ErgoValue.fromHex(
                            stakeBox["additionalRegisters"]["R5"]["serializedValue"]
                        ),
                    ],
                    contract=appKit.contractFromAddress(stakeBox["address"]),
                )
            )
        else:
            assetsToBurn[stakeBox["additionalRegisters"]["R5"]["renderedValue"]] = 1
        if penalty > 0:
            assetsToBurn[sc["stakedTokenID"]] = penalty

        ergsNeeded = (int(1e7) if (partial) else int(9e6)) + int(1e6)

        logging.debug("unstake::address")
        if req.address == "":
            changeAddress = userBox["address"]
        else:
            changeAddress = req.address

        userInputs = List[InputBox]
        tokensToSpend = {stakeBox["additionalRegisters"]["R5"]["renderedValue"]: 1}

        logging.debug("unstake::count utxos")
        if len(req.utxos) == 0:
            if len(req.addresses) == 0:
                userInputs = appKit.boxesToSpend(req.address, ergsNeeded, tokensToSpend)
            else:
                userInputs = appKit.boxesToSpendFromList(
                    req.addresses, ergsNeeded, tokensToSpend
                )
        else:
            userInputs = appKit.getBoxesById(req.utxos)
            if not ErgoAppKit.boxesCovered(userInputs, ergsNeeded, tokensToSpend):
                userInputs = appKit.boxesToSpend(req.address, ergsNeeded, tokensToSpend)
        if userInputs is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Could not find enough erg and/or tokens",
            )

        keyBox = None
        otherBoxes = []

        logging.debug("unstake::each user input")
        for box in userInputs:
            keyFound = False
            for token in box.getTokens():
                if (
                    token.getId().toString()
                    == stakeBox["additionalRegisters"]["R5"]["renderedValue"]
                ):
                    keyBox = box
                    keyFound = True
            if not keyFound:
                otherBoxes.append(box)

        logging.debug("unstake::other boxes")
        userInputs = [keyBox] + list(otherBoxes)
        userInputs = ErgoAppKit.cutOffExcessUTXOs(
            userInputs,
            ergsNeeded,
            {stakeBox["additionalRegisters"]["R5"]["renderedValue"]: 1},
        )
        inputs = appKit.getBoxesById([stakeStateBox["boxId"], req.stakeBox])
        unsignedTx = appKit.buildUnsignedTransaction(
            inputs + userInputs,
            outputs,
            int(1e6),
            Address.create(changeAddress).getErgoAddress(),
            tokensToBurn=assetsToBurn,
        )

        logging.warning(unsignedTx)

        logging.debug("unstake::txFormat")
        if req.txFormat == TXFormat.EIP_12:
            logging.debug("unstake::EIP_12")
            result = {
                "penalty": (penalty / 10 ** stakedTokenInfo["decimals"]),
                "unsignedTX": ErgoAppKit.unsignedTxToJson(unsignedTx),
            }
            return result

        if req.txFormat == TXFormat.ERGO_PAY:
            logging.debug("unstake::ERGO_PAY")
            reducedTx = appKit.reducedTx(unsignedTx)
            ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                reducedTx, address=changeAddress
            )
            cache.set(
                f"ergopay_signing_request_{unsignedTx.getId()}", ergoPaySigningRequest
            )
            return {
                "url": f"ergopay://api.ergopad.io/blockchain/signingRequest/{unsignedTx.getId()}"
            }

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to unstake, try again shortly or contact support if error continues.",
        )


def validPenalty(startTime: int):
    currentTime = int(time() * 1000)
    timeStaked = currentTime - startTime
    weeksStaked = int(timeStaked / week)
    return (
        0
        if (weeksStaked >= 8)
        else 5
        if (weeksStaked >= 6)
        else 12.5
        if (weeksStaked >= 4)
        else 20
        if (weeksStaked >= 2)
        else 25
    )


@r.post("/staked/", name="staking:staked")
def staked(req: AddressList, project: str = "ergopad"):
    return stakedv2(project=project, req=req)


@r.get("/status/", name="staking:status")
def stakingStatusV1(project: str = "ergopad"):
    return stakingStatus(project)


@r.get("/{project}/incentive/", name="staking:incentive")
def incentive(project: str = "ergopad"):
    appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)
    sc = stakingConfigsV1[project]
    params = {}
    params["stakedTokenID"] = hexstringToB64(sc["stakedTokenID"])
    params["stakePoolNFT"] = hexstringToB64(sc["stakePoolNFT"])
    params["emissionNFT"] = hexstringToB64(sc["emissionNFT"])
    params["stakeStateNFT"] = hexstringToB64(sc["stakeStateNFT"])
    params["stakeTokenID"] = hexstringToB64(sc["stakeTokenID"])

    emissionAddress = getErgoscript("emission", params=params)
    stakeAddress = getErgoscript("stake", params=params)
    stakeWallet = Wallet(stakeAddress)
    stakeErgoTreeBytes = bytes.fromhex(stakeWallet.ergoTree()[2:])
    stakeHash = b64encode(blake2b(stakeErgoTreeBytes, digest_size=32).digest()).decode(
        "utf-8"
    )

    params["stakeContractHash"] = stakeHash
    stakeStateAddress = getErgoscript("stakeState", params=params)

    stakeStateWallet = Wallet(stakeStateAddress)
    emissionWallet = Wallet(emissionAddress)

    stakeStateErgoTreeBytes = bytes.fromhex(stakeStateWallet.ergoTree()[2:])
    emissionErgoTreeBytes = bytes.fromhex(emissionWallet.ergoTree()[2:])

    stakeStateHash = blake2b(stakeStateErgoTreeBytes, digest_size=32).digest()
    logging.debug(stakeStateHash)
    emissionHash = blake2b(emissionErgoTreeBytes, digest_size=32).digest()
    logging.debug(emissionHash)

    with open(f"contracts/stakingIncentive.es") as f:
        script = f.read()
    incentiveTree = appKit.compileErgoScript(
        script,
        {
            "_emissionContractHash": ErgoAppKit.ergoValue(
                emissionHash, ErgoValueT.ByteArray
            ).getValue(),
            "_stakeStateContractHash": ErgoAppKit.ergoValue(
                stakeStateHash, ErgoValueT.ByteArray
            ).getValue(),
            "_stakeTokenID": ErgoAppKit.ergoValue(
                sc["stakeTokenID"], ErgoValueT.ByteArrayFromHex
            ).getValue(),
        },
    )

    return {
        "tree": incentiveTree.bytesHex(),
        "address": appKit.tree2Address(incentiveTree),
    }


@r.post("/stake/", name="staking:stake")
def stake(req: StakeRequest, project: str = "ergopad"):
    try:
        sc = stakingConfigsV1[project]
        logging.debug(f"stake::staked token info")
        stakedTokenInfo = getTokenInfo(sc["stakedTokenID"])

        logging.debug(f"stake::appkit")
        appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)

        logging.debug(f"stake::stakeAppkit.es")
        with open(f"contracts/stakeAppkit.es") as f:
            script = f.read()
        stakeTree = appKit.compileErgoScript(
            script,
            {
                "_stakeStateNFT": ErgoAppKit.ergoValue(
                    sc["stakeStateNFT"], ErgoValueT.ByteArrayFromHex
                ).getValue(),
                "_emissionNFT": ErgoAppKit.ergoValue(
                    sc["emissionNFT"], ErgoValueT.ByteArrayFromHex
                ).getValue(),
            },
        )

        logging.debug(f"stake::get NFT box")
        stakeStateBox = getNFTBox(sc["stakeStateNFT"])

        logging.debug(f"stake::token amount")
        tokenAmount = int(req.amount * 10 ** stakedTokenInfo["decimals"])

        logging.debug(f"stake::r4")
        r4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
        stakeStateOutput = appKit.buildOutBox(
            value=stakeStateBox["value"],
            tokens={
                stakeStateBox["assets"][0]["tokenId"]: stakeStateBox["assets"][0][
                    "amount"
                ],
                stakeStateBox["assets"][1]["tokenId"]: stakeStateBox["assets"][1][
                    "amount"
                ]
                - 1,
            },
            registers=[
                ErgoAppKit.ergoValue(
                    [
                        int(r4[0]) + tokenAmount,
                        int(r4[1]),
                        int(r4[2]) + 1,
                        int(r4[3]),
                        int(r4[4]),
                    ],
                    ErgoValueT.LongArray,
                )
            ],
            contract=appKit.contractFromAddress(stakeStateBox["address"]),
        )

        logging.debug(f"stake::build outbox stakeOutput")
        stakeOutput = appKit.buildOutBox(
            value=int(0.001 * nergsPerErg),
            tokens={
                stakeStateBox["assets"][1]["tokenId"]: 1,
                sc["stakedTokenID"]: tokenAmount,
            },
            registers=[
                ErgoAppKit.ergoValue(
                    [int(r4[1]), int(time() * 1000)], ErgoValueT.LongArray
                ),
                ErgoAppKit.ergoValue(
                    stakeStateBox["boxId"], ErgoValueT.ByteArrayFromHex
                ),
            ],
            contract=appKit.contractFromTree(stakeTree),
        )
        userInputs = List[InputBox]
        tokensToSpend = {sc["stakedTokenID"]: tokenAmount}

        try:
            logging.debug(f"stake::count utxos=={req.utxos}")
        except:
            pass
        if len(req.utxos) == 0:
            if len(req.addresses) == 0:
                userInputs = appKit.boxesToSpend(req.wallet, int(28e7), tokensToSpend)
            else:
                userInputs = appKit.boxesToSpendFromList(
                    req.addresses, int(28e7), tokensToSpend
                )
        else:
            userInputs = appKit.getBoxesById(req.utxos)
            if not ErgoAppKit.boxesCovered(userInputs, int(28e7), tokensToSpend):
                userInputs = appKit.boxesToSpend(req.wallet, int(28e7), tokensToSpend)
        if userInputs is None or len(userInputs) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Could not find enough erg and/or tokens",
            )

        logging.debug("stake::mint token")
        userOutput = appKit.mintToken(
            value=int(0.01 * nergsPerErg),
            tokenId=stakeStateBox["boxId"],
            tokenName=f'{stakedTokenInfo["name"]} Stake Key',
            tokenDesc=f'{{"originalAmountStaked": {req.amount}, "stakeTime": "{datetime.now()}"}}',
            mintAmount=1,
            decimals=0,
            contract=appKit.contractFromTree(userInputs[0].getErgoTree()),
        )

        logging.debug("stake::build outbox for fee")
        feeOutput = appKit.buildOutBox(
            value=int(0.25 * nergsPerErg),
            tokens=None,
            registers=None,
            contract=appKit.contractFromAddress(CFG.ergopadWallet),
        )

        logging.debug("stake::inputs/outputs")
        inputs = appKit.getBoxesById([stakeStateBox["boxId"]]) + userInputs
        outputs = [stakeStateOutput, stakeOutput, userOutput, feeOutput]

        logging.debug("stake::build utx")
        unsignedTx = appKit.buildUnsignedTransaction(
            inputs=inputs,
            outputs=outputs,
            fee=int(0.001 * nergsPerErg),
            sendChangeTo=Address.create(req.wallet).getErgoAddress(),
        )

        logging.debug(f"stake::txFormat=={req.txFormat}")
        if req.txFormat == TXFormat.EIP_12:
            logging.debug("stake::utx to json")
            return ErgoAppKit.unsignedTxToJson(unsignedTx)

        if req.txFormat == TXFormat.ERGO_PAY:
            logging.debug("stake::reduced tx")
            reducedTx = appKit.reducedTx(unsignedTx)
            ergoPaySigningRequest = ErgoAppKit.formErgoPaySigningRequest(
                reducedTx, address=req.wallet
            )
            cache.set(
                f"ergopay_signing_request_{unsignedTx.getId()}", ergoPaySigningRequest
            )
            return {
                "url": f"ergopay://api.ergopad.io/blockchain/signingRequest/{unsignedTx.getId()}"
            }

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to stake, try again shortly or contact support if error continues.",
        )


# bootstrap staking setup
@r.post("/bootstrap/", name="staking:bootstrap")
def bootstrapStaking(req: BootstrapRequest):
    try:
        stakedToken = getTokenInfo(req.stakedTokenID)
        stakedTokenDecimalMultiplier = 10 ** stakedToken["decimals"]

        stakeStateNFT = getTokenInfo(req.stakeStateNFT)
        if stakeStateNFT["name"] != f'{stakedToken["name"]} Stake State':
            return {
                "success": False,
                "Error": f"Wrong name for stake state NFT {stakeStateNFT['name']}",
            }
        if stakeStateNFT["emissionAmount"] > 1:
            return {
                "success": False,
                "Error": f"There should only be one {stakeStateNFT['name']}",
            }

        stakePoolNFT = getTokenInfo(req.stakePoolNFT)
        if stakePoolNFT["name"] != f'{stakedToken["name"]} Stake Pool':
            return {
                "success": False,
                "Error": f"Wrong name for stake pool NFT {stakePoolNFT['name']}",
            }
        if stakePoolNFT["emissionAmount"] > 1:
            return {
                "success": False,
                "Error": f"There should only be one {stakePoolNFT['name']}",
            }

        emissionNFT = getTokenInfo(req.emissionNFT)
        if emissionNFT["name"] != f'{stakedToken["name"]} Emission':
            return {
                "success": False,
                "Error": f"Wrong name for emission NFT {emissionNFT['name']}",
            }
        if emissionNFT["emissionAmount"] > 1:
            return {
                "success": False,
                "Error": f"There should only be one {emissionNFT['name']}",
            }

        stakeTokenID = getTokenInfo(req.stakeTokenID)
        if stakeTokenID["name"] != f'{stakedToken["name"]} Stake Token':
            return {
                "success": False,
                "Error": f"Wrong name for stake token {stakeTokenID['name']}",
            }
        if stakeTokenID["emissionAmount"] < 1000000000:
            return {
                "success": False,
                "Error": f"There should only be at least a billion {stakeTokenID['name']}",
            }

        params = {}
        params["stakedTokenID"] = hexstringToB64(req.stakedTokenID)
        params["stakePoolNFT"] = hexstringToB64(req.stakePoolNFT)
        params["emissionNFT"] = hexstringToB64(req.emissionNFT)
        params["stakeStateNFT"] = hexstringToB64(req.stakeStateNFT)
        params["stakeTokenID"] = hexstringToB64(req.stakeTokenID)

        emissionAddress = getErgoscript("emission", params=params)
        stakePoolAddress = getErgoscript("stakePool", params=params)
        stakeAddress = getErgoscript("stake", params=params)
        stakeWallet = Wallet(stakeAddress)
        stakeErgoTreeBytes = bytes.fromhex(stakeWallet.ergoTree()[2:])
        stakeHash = b64encode(
            blake2b(stakeErgoTreeBytes, digest_size=32).digest()
        ).decode("utf-8")

        params["stakeContractHash"] = stakeHash

        stakeStateAddress = getErgoscript("stakeState", params=params)
        stakePoolBox = {
            "address": stakePoolAddress,
            "value": int(0.001 * nergsPerErg),
            "registers": {
                "R4": encodeLongArray(
                    [int(req.emissionAmount * stakedTokenDecimalMultiplier)]
                )
            },
            "assets": [
                {"tokenId": req.stakePoolNFT, "amount": 1},
                {
                    "tokenId": req.stakedTokenID,
                    "amount": req.stakeAmount * stakedTokenDecimalMultiplier,
                },
            ],
        }

        stakeStateBox = {
            "address": stakeStateAddress,
            "value": int(0.001 * nergsPerErg),
            "registers": {
                "R4": encodeLongArray(
                    [
                        0,
                        0,
                        0,
                        req.emissionStart_ms - req.cycleDuration_ms,
                        req.cycleDuration_ms,
                    ]
                )
            },
            "assets": [
                {"tokenId": req.stakeStateNFT, "amount": 1},
                {"tokenId": req.stakeTokenID, "amount": 1000000000},
            ],
        }

        emissionBox = {
            "address": emissionAddress,
            "value": int(0.001 * nergsPerErg),
            "registers": {
                "R4": encodeLongArray(
                    [0, -1, 0, req.emissionAmount * stakedTokenDecimalMultiplier]
                )
            },
            "assets": [{"tokenId": req.emissionNFT, "amount": 1}],
        }

        res = {
            "requests": [stakeStateBox, emissionBox, stakePoolBox],
            "fee": int(0.001 * nergsPerErg),
        }
        return res

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to bootstrap, try again shortly or contact support if error continues.",
        )


@r.post("/{project}/stake/", name="staking:stake-v2")
def stakeV2(project: str, req: StakeRequest):
    try:
        if project in stakingConfigsV1:
            return stake(req, project)
        if project not in stakingConfigs:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"{project} does not have a staking config",
            )
        appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)
        config = stakingConfigs[project](appKit)
        tokenAmount = round(req.amount * 10**config.stakedTokenDecimals)
        assetsRequired = CreateStakeProxyTransaction.assetsRequired(config, tokenAmount)
        userInputs = appKit.boxesToSpendFromList(
            req.addresses, assetsRequired.nErgRequired, assetsRequired.tokensRequired
        )
        stakeProxyTx = CreateStakeProxyTransaction(
            userInputs, config, tokenAmount, req.wallet
        )

        if req.txFormat == TXFormat.EIP_12:
            return stakeProxyTx.eip12

        if req.txFormat == TXFormat.ERGO_PAY:
            cache.set(
                f"ergopay_signing_request_{stakeProxyTx.unsignedTx.getId()}",
                stakeProxyTx.ergoPaySigningRequest,
            )
            return {
                "url": f"ergopay://api.ergopad.io/blockchain/signingRequest/{stakeProxyTx.unsignedTx.getId()}"
            }

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to stake, please make sure you have at least 0.5 erg in wallet.",
        )


@r.post("/{project}/unstake/", name="staking:unstake-v2")
def unstakev2(project: str, req: UnstakeRequest):
    try:
        if project in stakingConfigsV1:
            return unstake(req, project)
        if project not in stakingConfigs:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"{project} does not have a staking config",
            )
        appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)
        config = stakingConfigs[project](appKit)
        stakeInput = appKit.getBoxesById([req.stakeBox])[0]
        tokenAmount = round(req.amount * 10**config.stakedTokenDecimals)
        remaining = stakeInput.getTokens()[0].getValue() - tokenAmount
        if remaining > 0 and remaining < 1000:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"A partial unstake needs to leave at least {remaining/10**config.stakedTokenDecimals} tokens remaining",
            )
        assetsRequired = CreateUnstakeProxyTransaction.assetsRequired(
            config, tokenAmount, stakeInput
        )
        userInputs = appKit.boxesToSpendFromList(
            req.addresses, assetsRequired.nErgRequired, assetsRequired.tokensRequired
        )
        unstakeProxyTx = CreateUnstakeProxyTransaction(
            userInputs,
            stakeInput,
            config,
            req.amount * 10**config.stakedTokenDecimals,
            req.address,
        )

        if req.txFormat == TXFormat.EIP_12:
            return unstakeProxyTx.eip12

        if req.txFormat == TXFormat.ERGO_PAY:
            cache.set(
                f"ergopay_signing_request_{unstakeProxyTx.unsignedTx.getId()}",
                unstakeProxyTx.ergoPaySigningRequest,
            )
            return {
                "url": f"ergopay://api.ergopad.io/blockchain/signingRequest/{unstakeProxyTx.unsignedTx.getId()}"
            }

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to unstake, please make sure you have at least 0.5 erg in wallet.",
        )


@r.post("/{project}/addstake/", name="staking:addstake-v2")
def addstake(project: str, req: UnstakeRequest):
    try:
        if project not in stakingConfigs:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"{project} does not have a staking config",
            )
        appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)
        config = stakingConfigs[project](appKit)
        stakeInput = appKit.getBoxesById([req.stakeBox])[0]
        tokenAmount = round(req.amount * 10**config.stakedTokenDecimals)
        assetsRequired = CreateAddStakeProxyTransaction.assetsRequired(
            config, tokenAmount, stakeInput
        )
        userInputs = appKit.boxesToSpendFromList(
            req.addresses, assetsRequired.nErgRequired, assetsRequired.tokensRequired
        )
        addStakeProxyTx = CreateAddStakeProxyTransaction(
            userInputs, stakeInput, config, tokenAmount, req.address
        )

        if req.txFormat == TXFormat.EIP_12:
            return addStakeProxyTx.eip12

        if req.txFormat == TXFormat.ERGO_PAY:
            cache.set(
                f"ergopay_signing_request_{addStakeProxyTx.unsignedTx.getId()}",
                addStakeProxyTx.ergoPaySigningRequest,
            )
            return {
                "url": f"ergopay://api.ergopad.io/blockchain/signingRequest/{addStakeProxyTx.unsignedTx.getId()}"
            }

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to add stake, please make sure you have at least 0.5 erg in wallet.",
        )


@r.get("/{project}/status/", name="staking:xstatus-v2")
def stakingStatus(project: str):
    try:
        sql = text(
            f"""           
            select str4, plr4, dcml
            from token_status
            where token_name = :project
        """
        )
        with engDanaides.begin() as con:
            res = con.execute(sql, {"project": project}).fetchone()

        totalStaked = ErgoValue.fromHex(res["str4"]).getValue().apply(0)
        cycleEmission = ErgoValue.fromHex(res["plr4"]).getValue().apply(0)
        dailyEmission = (
            cycleEmission
            * 86400000
            / ErgoValue.fromHex(res["str4"]).getValue().apply(4)
        )

        apy = round(dailyEmission * 36500 / totalStaked, 2)

        ret = {
            "Total amount staked": totalStaked / 10 ** res["dcml"],
            "Staking boxes": ErgoValue.fromHex(res["str4"]).getValue().apply(2),
            "Cycle start": ErgoValue.fromHex(res["str4"]).getValue().apply(3),
            "APY": apy,
        }

        # cache and return
        cache.set(f"get_api_staking_status_{project}", ret)
        return ret

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to find status, try again shortly or contact support if error continues.",
        )


@r.post("/{project}/staked/", name="staking:staked-v2")
def stakedv2(project: str, req: AddressList):
    try:
        logging.debug("stakedv2.init")
        stakePerAddress = {}
        totalStaked = 0
        penaltyPct = None
        penaltyEndTime = None
        tokenName = ""
        wallet_addresses = "'" + ("','".join(req.addresses)) + "'"

        if VERBOSE:
            logging.debug("stakedv2.sql")
        sql = text(
            f"""
            select 
                  s.address
                , s.project_name
                , s.token_id
                , s.box_id
                , s.stakekey_token_id
                , s.amount
                , s.penalty
                , t.token_name
            from staking s
                join tokens t on t.token_id = s.token_id
            where address in ({wallet_addresses})
                and project_name = :project
        """
        )
        with engDanaides.begin() as con:
            res = con.execute(sql, {"project": project}).fetchall()

        for row in res:
            if VERBOSE:
                logging.debug(f"""row {row['address']}""")
            # properly convert amount
            amt = Decimal(0)
            try:
                amt = Decimal(row["amount"])
            except:
                pass
            totalStaked += amt

            # init stakePerAddress
            if row["address"] not in stakePerAddress:
                if VERBOSE:
                    logging.debug("stakedv2.init2")
                stakePerAddress[row["address"]] = {
                    "totalStaked": Decimal(0),
                    "stakeBoxes": [],
                }
                tokenName = row["token_name"]

            # penalty
            if VERBOSE:
                logging.debug("stakedv2.penalty")
            # TODO: is this the right way to filter out what has penalty?
            if project in ["ergopad", "egio"]:
                try:
                    penalty = ErgoValue.fromHex(row["penalty"]).getValue().apply(1)
                    if VERBOSE:
                        logging.debug(f"penalty: {penalty}")
                    penaltyPct = validPenalty(penalty)
                    if VERBOSE:
                        logging.debug(f"penalty: {penaltyPct}")
                    penaltyEndTime = int(penalty + 8 * week)
                    if VERBOSE:
                        logging.debug(f"penalty: {penaltyEndTime}")
                except Exception as e:
                    if VERBOSE:
                        logging.debug(f"invalid penalty {e}")
                    pass

            # summarize
            if VERBOSE:
                logging.debug("stakedv2.summary")
            stakePerAddress[row["address"]]["totalStaked"] += amt
            spa = {
                "boxId": row["box_id"],
                "stakeKeyId": row["stakekey_token_id"],
                "stakeAmount": amt,
            }
            if penaltyPct != None:
                spa["penaltyPct"] = penaltyPct
                spa["penaltyEndTime"] = penaltyEndTime
            stakePerAddress[row["address"]]["stakeBoxes"].append(spa)

        if VERBOSE:
            logging.debug("stakedv2.return")
        return {
            "project": project,
            "tokenName": tokenName,
            "totalStaked": totalStaked,
            "addresses": stakePerAddress,
        }

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to determine staked value.",
        )


@r.post("/staked-all/", name="staking:staked-all")
def allStaked(req: AddressList):
    try:
        logging.debug("allStaked.init")
        stakePerAddress = {}
        projects = {}
        totalStaked = {}
        tokenName = {}
        wallet_addresses = "'" + ("','".join(req.addresses)) + "'"

        if VERBOSE:
            logging.debug("allStaked.sql")
        sql = text(
            f"""
            select 
                  s.address
                , s.project_name
                , s.token_id
                , s.box_id
                , s.stakekey_token_id
                , s.amount
                , s.penalty
                , t.token_name
            from staking s
                join tokens t on t.token_id = s.token_id
            where address in ({wallet_addresses})
        """
        )
        with engDanaides.begin() as con:
            res = con.execute(sql).fetchall()

        for row in res:
            if VERBOSE:
                logging.debug(f"""row {row['address']}""")

            # split out by project
            project = row["project_name"]
            if project not in projects:
                projects[project] = []

            # properly convert amount
            amt = Decimal(0)
            try:
                amt = Decimal(row["amount"])
            except:
                pass
            if project not in totalStaked:
                totalStaked[project] = Decimal(0)
            totalStaked[project] += amt

            # init stakePerAddress
            if project not in stakePerAddress:
                stakePerAddress[project] = {}
            if row["address"] not in stakePerAddress[project]:
                if VERBOSE:
                    logging.debug("allStaked.init2")
                stakePerAddress[project][row["address"]] = {
                    "totalStaked": Decimal(0),
                    "stakeBoxes": [],
                }
                if VERBOSE:
                    logging.debug("allStaked.init3")
                tokenName[project] = row["token_name"]

            # summarize
            summary = {}
            if VERBOSE:
                logging.debug("allStaked.summary")
            stakePerAddress[project][row["address"]]["totalStaked"] += amt
            summary["boxId"] = row["box_id"]
            summary["stakeKeyId"] = row["stakekey_token_id"]
            summary["stakeAmount"] = amt
            if project in ["ergopad", "egio"]:
                penalty = ErgoValue.fromHex(row["penalty"]).getValue().apply(1)
                penaltyPct = validPenalty(penalty)
                penaltyEndTime = int(penalty + 8 * week)
                summary["penaltyPct"] = penaltyPct
                summary["penaltyEndTime"] = penaltyEndTime
            stakePerAddress[project][row["address"]]["stakeBoxes"].append(summary)

        for project in projects:
            projects[project].append(
                {
                    "project": project,
                    "tokenName": tokenName[project],
                    "totalStaked": totalStaked[project],
                    "addresses": stakePerAddress[project],
                }
            )

        if VERBOSE:
            logging.debug("allStaked.return")
        # return projects
        return [projects[p][0] for p in projects]

    except Exception as e:
        logging.error(f"ERR:{myself()}: ({e})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"ERR:{myself()}: Unable to determine staked value.",
        )


########################################
########## STAKING CONFIG CMS ##########
########################################


@r.get("/config", response_model_exclude_none=True, name="staking-cms:all-config")
def staking_config_list_cms(
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
def staking_config_cms(
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
def staking_config_create_cms(
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
def staking_config_edit_cms(
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
def staking_config_delete_cms(
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
