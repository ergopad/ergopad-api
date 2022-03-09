from config import Config, Network

import jpype
import jpype.imports
from jpype.types import *
from jpype import JImplements, JOverride

jpype.startJVM()
jpype.addClassPath('/app/jars/*')

from org.ergoplatform import ErgoAddressEncoder
from org.ergoplatform.appkit import ConstantsBuilder, ErgoContract, NetworkType
from org.ergoplatform.restapi.client import ApiClient
from org.ergoplatform.explorer.client import ExplorerApiClient
from org.ergoplatform.appkit.impl import BlockchainContextBuilderImpl

CFG = Config[Network]

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

    def getBlockChainContext(self):
        return BlockchainContextBuilderImpl(self._client, self._explorer, self._networkType).build()

    def tree2Address(self, ergoTree):
        return self._addrEnc.fromProposition(ergoTree).get().toString()

    def NetworkType(networkType: str):
        if networkType.lower()=="testnet":
            return NetworkType.TESTNET
        else:
            return NetworkType.MAINNET