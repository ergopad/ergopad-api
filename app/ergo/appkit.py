import typing
from config import Config, Network
import jpype
import jpype.imports
from jpype.types import *
from jpype import JImplements, JOverride
from enum import Enum
from typing import Dict, List, TypeVar

try:
    jpype.addClassPath('../jars/*')
    jpype.addClassPath('./jars/*')
    jpype.startJVM(None, convertStrings=True)
except OSError:
    print("JVM already running")


from org.ergoplatform import DataInput, ErgoAddress, ErgoAddressEncoder
from org.ergoplatform.appkit import Address, BlockchainContext, BoxOperations, ConstantsBuilder, ErgoClient, ErgoContract, ErgoToken, ErgoType, ErgoValue, InputBox, Iso, JavaHelpers, NetworkType, OutBox, PreHeader, ReducedTransaction, RestApiErgoClient, SignedTransaction, UnsignedTransaction
from org.ergoplatform.restapi.client import ApiClient, Asset, ErgoTransactionDataInput, ErgoTransactionOutput, ErgoTransactionUnsignedInput, Registers, TransactionSigningRequest, UnsignedErgoTransaction, WalletApi
from org.ergoplatform.explorer.client import ExplorerApiClient
from org.ergoplatform.appkit.impl import BlockchainContextBuilderImpl, BlockchainContextImpl, ErgoNodeFacade, ErgoTreeContract, ExplorerFacade, ScalaBridge, SignedTransactionImpl, UnsignedTransactionImpl
from special.collection import Coll
from sigmastate.Values import ErgoTree
from scala import Byte as SByte, Long as SLong
import java
import scala
from java.math import BigInteger
from java.lang import NullPointerException

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
        self._explorerUrl = explorerUrl.replace("/api/v1","")
        if self._explorerUrl!="":
            self._explorer = ExplorerApiClient(self._explorerUrl)
        else:
            self._explorer = None
        self._addrEnc = ErgoAddressEncoder(self._networkType.networkPrefix)

    def compileErgoScript(self, ergoScript: str, constants: dict[str,typing.Any] = {}) -> ErgoTree:
        return JavaHelpers.compile(constants,ergoScript,self._networkType.networkPrefix)

    def getBlockChainContext(self) -> BlockchainContextImpl:
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
    
    def mintToken(self, value: int, tokenId: str, tokenName: str, tokenDesc: str, mintAmount: int, decimals: int, contract: ErgoContract) -> OutBox:
        ctx = self.getBlockChainContext()
        tb = ctx.newTxBuilder()
        
        return tb.outBoxBuilder().contract(contract).value(value).mintToken(ErgoToken(tokenId,mintAmount),tokenName,tokenDesc,decimals).build()

    def buildInputBox(self,value: int, tokens: Dict[str,int], registers, contract) -> InputBox:
        return self.buildOutBox(value, tokens, registers, contract).convertToInputWith("ce552663312afc2379a91f803c93e2b10b424f176fbc930055c10def2fd88a5d", 0)

    def boxesToSpend(self, address: str, nergToSpend: int, tokensToSpend: dict[str,int] = {}) -> list[InputBox]:
        ctx = self.getBlockChainContext()
        tts = []
        for token in tokensToSpend:
            tts.append(ErgoToken(token,tokensToSpend[token]))
        try:
            coveringBoxes = ctx.getCoveringBoxesFor(Address.create(address),nergToSpend,java.util.ArrayList(tts))
        except NullPointerException as e:
            err = ""
            for stackTraceElement in e.getStackTrace():
                err = '\n'.join([err,stackTraceElement.toString()])
            err = '\n'.join([err,str(e.getMessage())])
            logging.info(err)
        if coveringBoxes.isCovered:
            return coveringBoxes.getBoxes()
        else:
            return None

    def ergoValue(self, value, t: ErgoValueT):
        if t == ErgoValueT.Long:
            res = ErgoValue.of(JLong(value))
            return res
        if t == ErgoValueT.ByteArrayFromHex:
            return ErgoValue.of(bytes.fromhex(value))
        if t == ErgoValueT.LongArray:
            collVal = []
            for l in value:
                collVal.append(JLong(l))
            res = ErgoValue.of(collVal,ErgoType.longType())
            return res
        if t == ErgoValueT.ByteArray:
            res = ErgoValue.of(value)
            return res

    def dummyContract(self) -> ErgoContract:
        return ErgoTreeContract(Address.create("4MQyML64GnzMxZgm").getErgoAddress().script(),self._networkType)

    def contractFromTree(self,tree: ErgoTree) -> ErgoContract:
        return ErgoTreeContract(tree,self._networkType)

    def contractFromAddress(self,addr: str) -> ErgoContract:
        return ErgoTreeContract(Address.create(addr).getErgoAddress().script(),self._networkType)

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

    def sendTransaction(self, signedTx: SignedTransaction) -> str:
        ctx = self.getBlockChainContext()
        return ctx.sendTransaction(signedTx)

    def signTransactionWithNode(self, unsignedTx: UnsignedTransactionImpl) -> SignedTransaction:
        signRequest = TransactionSigningRequest()
        unsignedErgoTx = UnsignedErgoTransaction()
        unsignedErgoLikeTx = unsignedTx.getTx()
        for i in range(int(unsignedErgoLikeTx.inputs().length())):
            input = unsignedErgoLikeTx.inputs().apply(JInt(i))
            unsignedInput = ErgoTransactionUnsignedInput()
            unsignedInput.setBoxId(unsignedTx.getInputs()[i].getId().toString())
            unsignedInput.setExtension(scala.collection.JavaConversions.mapAsJavaMap(input.extension().values()))
            unsignedErgoTx = unsignedErgoTx.addInputsItem(unsignedInput)
        unsignedErgoTx.setDataInputs(Iso.inverseIso(Iso.JListToIndexedSeq(ScalaBridge.isoErgoTransactionDataInput())).to(unsignedErgoLikeTx.dataInputs()))
        unsignedErgoTx.setOutputs(Iso.inverseIso(Iso.JListToIndexedSeq(ScalaBridge.isoErgoTransactionOutput())).to(unsignedErgoLikeTx.outputs()))
        signRequest.setTx(unsignedErgoTx)
        api = self._client.createService(WalletApi)
        ergoTx = api.walletTransactionSign(signRequest).execute().body()
        tx = ScalaBridge.isoErgoTransaction().to(ergoTx)
        signedTx = SignedTransactionImpl(self.getBlockChainContext(),tx,0)
        return signedTx

        

    


