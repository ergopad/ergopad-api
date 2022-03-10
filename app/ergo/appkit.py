from app.config import Config, Network
import jpype
import jpype.imports
from jpype.types import *
from jpype import JImplements, JOverride
from enum import Enum
from typing import Dict, List, TypeVar

jpype.addClassPath('D:/ergo/ergopad-api/app/jars/*')
jpype.startJVM(None, convertStrings=True)

from org.ergoplatform import DataInput, ErgoAddress, ErgoAddressEncoder
from org.ergoplatform.appkit import Address, BlockchainContext, ConstantsBuilder, ErgoToken, ErgoValue, InputBox, NetworkType, OutBox, PreHeader, SignedTransaction, UnsignedTransaction
from org.ergoplatform.restapi.client import ApiClient
from org.ergoplatform.explorer.client import ExplorerApiClient
from org.ergoplatform.appkit.impl import BlockchainContextBuilderImpl, ErgoTreeContract
from special.collection import Coll
from scala import Byte as SByte, Long as SLong
import java
from java.math import BigInteger

DEBUG = True # CFG.DEBUG

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

CFG = Config[Network]

class ErgoValueT(Enum):
    Long = 0,
    ByteArray = 1,
    LongArray = 2,
    ByteArrayFromHex = 4

class ErgoAppKit:
    
    def __init__(self,nodeUrl: str, networkType: str, explorerUrl: str):
        self._nodeUrl = nodeUrl
        self._networkType = ErgoAppKit.NetworkType(networkType)
        self._client = ApiClient(self._nodeUrl, "ApiKeyAuth", CFG.ergopadApiKey)
        self._explorerUrl = explorerUrl
        if self._explorerUrl=="":
            self._explorer = ExplorerApiClient(self._explorerUrl)
        else:
            self._explorer = None
        self._addrEnc = ErgoAddressEncoder(self._networkType.networkPrefix)

    def compileErgoScript(self, ergoScript: str):
        ctx = self.getBlockChainContext()
        return ctx.compileContract(ConstantsBuilder.create().build(),ergoScript)

    def getBlockChainContext(self) -> BlockchainContext:
        return BlockchainContextBuilderImpl(self._client, self._explorer, self._networkType).build()

    def tree2Address(self, ergoTree):
        return self._addrEnc.fromProposition(ergoTree).get().toString()

    def NetworkType(networkType: str):
        if networkType.lower()=="testnet":
            return NetworkType.TESTNET
        else:
            return NetworkType.MAINNET

    def buildOutBox(self,value: int, tokens: Dict[str,int], registers, contract) -> OutBox:
        ctx = self.getBlockChainContext()
        tb = ctx.newTxBuilder()
        ergoTokens = []

        for token in tokens.keys():
            ergoTokens.append(ErgoToken(token,tokens[token]))
        tb = tb.outBoxBuilder().contract(contract).value(value).tokens(ergoTokens)

        if registers is not None:
            tb = tb.registers(registers)

        return tb.build()

    def buildInputBox(self,value: int, tokens: Dict[str,int], registers, contract) -> InputBox:
        return self.buildOutBox(value, tokens, registers, contract).convertToInputWith("ce552663312afc2379a91f803c93e2b10b424f176fbc930055c10def2fd88a5d", 0)

    def ergoValue(self, value, t: ErgoValueT):
        if t == ErgoValueT.Long:
            res = ErgoValue.of(JLong(value))
            return res
        if t == ErgoValueT.ByteArrayFromHex:
            return ErgoValue.of(bytes.fromhex(value))

    def dummyContract(self):
        return ErgoTreeContract(Address.create("4MQyML64GnzMxZgm").getErgoAddress().script(),self._networkType)

    def preHeader(self, timestamp: int = None) -> PreHeader:
        ctx = self.getBlockChainContext()
        phb = ctx.createPreHeader()
        if timestamp is not None:
            phb = phb.timestamp(JLong(timestamp))
        return phb.build()

    def buildUnsignedTransaction(self, inputs: List[InputBox], outputs: List[OutBox], fee: int, sendChangeTo: ErgoAddress, dataInputs: List[DataInput] = None, preHeader: PreHeader = None) -> UnsignedTransaction:
        ctx = self.getBlockChainContext()
        tb = ctx.newTxBuilder()
        tb = tb.boxesToSpend(java.util.ArrayList(inputs)).fee(fee).outputs(outputs).sendChangeTo(sendChangeTo)
        if preHeader is not None:
            tb = tb.preHeader(preHeader)
        if dataInputs is not None:
            tb = tb.withDataInputs(java.util.ArrayList(dataInputs))
        return tb.build()

    def signTransaction(self, unsignedTx: UnsignedTransaction) -> SignedTransaction:
        ctx = self.getBlockChainContext()
        prover = ctx.newProverBuilder().build()
        return prover.sign(unsignedTx)


