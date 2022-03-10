import java.util
import typing



class AdditionalRegister:
    serializedValue: str = ...
    sigmaType: str = ...
    renderedValue: str = ...
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class AdditionalRegisters(java.util.HashMap[str, AdditionalRegister]):
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class AdditionalRegisters1(java.util.HashMap[str, str]):
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class AssetInfo:
    def __init__(self): ...
    def amount(self, long: int) -> 'AssetInfo': ...
    def boxId(self, string: str) -> 'AssetInfo': ...
    def decimals(self, integer: int) -> 'AssetInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAmount(self) -> int: ...
    def getBoxId(self) -> str: ...
    def getDecimals(self) -> int: ...
    def getHeaderId(self) -> str: ...
    def getIndex(self) -> int: ...
    def getName(self) -> str: ...
    def getTokenId(self) -> str: ...
    def getType(self) -> str: ...
    def hashCode(self) -> int: ...
    def headerId(self, string: str) -> 'AssetInfo': ...
    def index(self, integer: int) -> 'AssetInfo': ...
    def name(self, string: str) -> 'AssetInfo': ...
    def setAmount(self, long: int) -> None: ...
    def setBoxId(self, string: str) -> None: ...
    def setDecimals(self, integer: int) -> None: ...
    def setHeaderId(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setName(self, string: str) -> None: ...
    def setTokenId(self, string: str) -> None: ...
    def setType(self, string: str) -> None: ...
    def toString(self) -> str: ...
    def tokenId(self, string: str) -> 'AssetInfo': ...
    def type(self, string: str) -> 'AssetInfo': ...

class AssetInstanceInfo:
    def __init__(self): ...
    def amount(self, long: int) -> 'AssetInstanceInfo': ...
    def decimals(self, integer: int) -> 'AssetInstanceInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAmount(self) -> int: ...
    def getDecimals(self) -> int: ...
    def getIndex(self) -> int: ...
    def getName(self) -> str: ...
    def getTokenId(self) -> str: ...
    def getType(self) -> str: ...
    def hashCode(self) -> int: ...
    def index(self, integer: int) -> 'AssetInstanceInfo': ...
    def name(self, string: str) -> 'AssetInstanceInfo': ...
    def setAmount(self, long: int) -> None: ...
    def setDecimals(self, integer: int) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setName(self, string: str) -> None: ...
    def setTokenId(self, string: str) -> None: ...
    def setType(self, string: str) -> None: ...
    def toString(self) -> str: ...
    def tokenId(self, string: str) -> 'AssetInstanceInfo': ...
    def type(self, string: str) -> 'AssetInstanceInfo': ...

class BadRequest:
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def getReason(self) -> str: ...
    def getStatus(self) -> int: ...
    def hashCode(self) -> int: ...
    def reason(self, string: str) -> 'BadRequest': ...
    def setReason(self, string: str) -> None: ...
    def setStatus(self, integer: int) -> None: ...
    def status(self, integer: int) -> 'BadRequest': ...
    def toString(self) -> str: ...

class Balance:
    def __init__(self): ...
    def addTokensItem(self, tokenAmount: 'TokenAmount') -> 'Balance': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getNanoErgs(self) -> int: ...
    def getTokens(self) -> java.util.List['TokenAmount']: ...
    def hashCode(self) -> int: ...
    def nanoErgs(self, long: int) -> 'Balance': ...
    def setNanoErgs(self, long: int) -> None: ...
    def setTokens(self, list: java.util.List['TokenAmount']) -> None: ...
    def toString(self) -> str: ...
    def tokens(self, list: java.util.List['TokenAmount']) -> 'Balance': ...

class BlockExtensionInfo:
    def __init__(self): ...
    def digest(self, string: str) -> 'BlockExtensionInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def fields(self, fields: 'Fields') -> 'BlockExtensionInfo': ...
    def getDigest(self) -> str: ...
    def getFields(self) -> 'Fields': ...
    def getHeaderId(self) -> str: ...
    def hashCode(self) -> int: ...
    def headerId(self, string: str) -> 'BlockExtensionInfo': ...
    def setDigest(self, string: str) -> None: ...
    def setFields(self, fields: 'Fields') -> None: ...
    def setHeaderId(self, string: str) -> None: ...
    def toString(self) -> str: ...

class BlockInfo:
    def __init__(self): ...
    def difficulty(self, long: int) -> 'BlockInfo': ...
    def epoch(self, integer: int) -> 'BlockInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getDifficulty(self) -> int: ...
    def getEpoch(self) -> int: ...
    def getHeight(self) -> int: ...
    def getId(self) -> str: ...
    def getMiner(self) -> 'MinerInfo': ...
    def getMinerReward(self) -> int: ...
    def getSize(self) -> int: ...
    def getTimestamp(self) -> int: ...
    def getTransactionsCount(self) -> int: ...
    def getVersion(self) -> int: ...
    def hashCode(self) -> int: ...
    def height(self, integer: int) -> 'BlockInfo': ...
    def id(self, string: str) -> 'BlockInfo': ...
    def miner(self, minerInfo: 'MinerInfo') -> 'BlockInfo': ...
    def minerReward(self, long: int) -> 'BlockInfo': ...
    def setDifficulty(self, long: int) -> None: ...
    def setEpoch(self, integer: int) -> None: ...
    def setHeight(self, integer: int) -> None: ...
    def setId(self, string: str) -> None: ...
    def setMiner(self, minerInfo: 'MinerInfo') -> None: ...
    def setMinerReward(self, long: int) -> None: ...
    def setSize(self, integer: int) -> None: ...
    def setTimestamp(self, long: int) -> None: ...
    def setTransactionsCount(self, integer: int) -> None: ...
    def setVersion(self, integer: int) -> None: ...
    def size(self, integer: int) -> 'BlockInfo': ...
    def timestamp(self, long: int) -> 'BlockInfo': ...
    def toString(self) -> str: ...
    def transactionsCount(self, integer: int) -> 'BlockInfo': ...
    def version(self, integer: int) -> 'BlockInfo': ...

class BlockReferencesInfo:
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def getNextId(self) -> str: ...
    def getPreviousId(self) -> str: ...
    def hashCode(self) -> int: ...
    def nextId(self, string: str) -> 'BlockReferencesInfo': ...
    def previousId(self, string: str) -> 'BlockReferencesInfo': ...
    def setNextId(self, string: str) -> None: ...
    def setPreviousId(self, string: str) -> None: ...
    def toString(self) -> str: ...

class BlockSummary:
    def __init__(self): ...
    def block(self, fullBlockInfo: 'FullBlockInfo') -> 'BlockSummary': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getBlock(self) -> 'FullBlockInfo': ...
    def getReferences(self) -> BlockReferencesInfo: ...
    def hashCode(self) -> int: ...
    def references(self, blockReferencesInfo: BlockReferencesInfo) -> 'BlockSummary': ...
    def setBlock(self, fullBlockInfo: 'FullBlockInfo') -> None: ...
    def setReferences(self, blockReferencesInfo: BlockReferencesInfo) -> None: ...
    def toString(self) -> str: ...

class BoxQuery:
    def __init__(self): ...
    def addAssetsItem(self, string: str) -> 'BoxQuery': ...
    def assets(self, list: java.util.List[str]) -> 'BoxQuery': ...
    def constants(self, map: typing.Union[java.util.Map[str, str], typing.Mapping[str, str]]) -> 'BoxQuery': ...
    def equals(self, object: typing.Any) -> bool: ...
    def ergoTreeTemplateHash(self, string: str) -> 'BoxQuery': ...
    def getAssets(self) -> java.util.List[str]: ...
    def getConstants(self) -> java.util.Map[str, str]: ...
    def getErgoTreeTemplateHash(self) -> str: ...
    def getRegisters(self) -> java.util.Map[str, str]: ...
    def hashCode(self) -> int: ...
    def putConstantsItem(self, string: str, string2: str) -> 'BoxQuery': ...
    def putRegistersItem(self, string: str, string2: str) -> 'BoxQuery': ...
    def registers(self, map: typing.Union[java.util.Map[str, str], typing.Mapping[str, str]]) -> 'BoxQuery': ...
    def setAssets(self, list: java.util.List[str]) -> None: ...
    def setConstants(self, map: typing.Union[java.util.Map[str, str], typing.Mapping[str, str]]) -> None: ...
    def setErgoTreeTemplateHash(self, string: str) -> None: ...
    def setRegisters(self, map: typing.Union[java.util.Map[str, str], typing.Mapping[str, str]]) -> None: ...
    def toString(self) -> str: ...

class DataInputInfo:
    def __init__(self): ...
    def addAssetsItem(self, assetInstanceInfo: AssetInstanceInfo) -> 'DataInputInfo': ...
    def additionalRegisters(self, additionalRegisters: AdditionalRegisters) -> 'DataInputInfo': ...
    def address(self, string: str) -> 'DataInputInfo': ...
    def assets(self, list: java.util.List[AssetInstanceInfo]) -> 'DataInputInfo': ...
    def boxId(self, string: str) -> 'DataInputInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def ergoTree(self, string: str) -> 'DataInputInfo': ...
    def getAdditionalRegisters(self) -> AdditionalRegisters: ...
    def getAddress(self) -> str: ...
    def getAssets(self) -> java.util.List[AssetInstanceInfo]: ...
    def getBoxId(self) -> str: ...
    def getErgoTree(self) -> str: ...
    def getIndex(self) -> int: ...
    def getOutputBlockId(self) -> str: ...
    def getOutputIndex(self) -> int: ...
    def getOutputTransactionId(self) -> str: ...
    def getValue(self) -> int: ...
    def hashCode(self) -> int: ...
    def index(self, integer: int) -> 'DataInputInfo': ...
    def outputBlockId(self, string: str) -> 'DataInputInfo': ...
    def outputIndex(self, integer: int) -> 'DataInputInfo': ...
    def outputTransactionId(self, string: str) -> 'DataInputInfo': ...
    def setAdditionalRegisters(self, additionalRegisters: AdditionalRegisters) -> None: ...
    def setAddress(self, string: str) -> None: ...
    def setAssets(self, list: java.util.List[AssetInstanceInfo]) -> None: ...
    def setBoxId(self, string: str) -> None: ...
    def setErgoTree(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setOutputBlockId(self, string: str) -> None: ...
    def setOutputIndex(self, integer: int) -> None: ...
    def setOutputTransactionId(self, string: str) -> None: ...
    def setValue(self, long: int) -> None: ...
    def toString(self) -> str: ...
    def value(self, long: int) -> 'DataInputInfo': ...

class DataInputInfo1:
    def __init__(self): ...
    def address(self, string: str) -> 'DataInputInfo1': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAddress(self) -> str: ...
    def getId(self) -> str: ...
    def getIndex(self) -> int: ...
    def getOutputIndex(self) -> int: ...
    def getOutputTransactionId(self) -> str: ...
    def getTransactionId(self) -> str: ...
    def getValue(self) -> int: ...
    def hashCode(self) -> int: ...
    def id(self, string: str) -> 'DataInputInfo1': ...
    def index(self, integer: int) -> 'DataInputInfo1': ...
    def outputIndex(self, integer: int) -> 'DataInputInfo1': ...
    def outputTransactionId(self, string: str) -> 'DataInputInfo1': ...
    def setAddress(self, string: str) -> None: ...
    def setId(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setOutputIndex(self, integer: int) -> None: ...
    def setOutputTransactionId(self, string: str) -> None: ...
    def setTransactionId(self, string: str) -> None: ...
    def setValue(self, long: int) -> None: ...
    def toString(self) -> str: ...
    def transactionId(self, string: str) -> 'DataInputInfo1': ...
    def value(self, long: int) -> 'DataInputInfo1': ...

class EpochParameters:
    def __init__(self): ...
    def blockVersion(self, integer: int) -> 'EpochParameters': ...
    def dataInputCost(self, integer: int) -> 'EpochParameters': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getBlockVersion(self) -> int: ...
    def getDataInputCost(self) -> int: ...
    def getHeight(self) -> int: ...
    def getId(self) -> int: ...
    def getInputCost(self) -> int: ...
    def getMaxBlockCost(self) -> int: ...
    def getMaxBlockSize(self) -> int: ...
    def getMinValuePerByte(self) -> int: ...
    def getOutputCost(self) -> int: ...
    def getStorageFeeFactor(self) -> int: ...
    def getTokenAccessCost(self) -> int: ...
    def hashCode(self) -> int: ...
    def height(self, integer: int) -> 'EpochParameters': ...
    def id(self, integer: int) -> 'EpochParameters': ...
    def inputCost(self, integer: int) -> 'EpochParameters': ...
    def maxBlockCost(self, integer: int) -> 'EpochParameters': ...
    def maxBlockSize(self, integer: int) -> 'EpochParameters': ...
    def minValuePerByte(self, integer: int) -> 'EpochParameters': ...
    def outputCost(self, integer: int) -> 'EpochParameters': ...
    def setBlockVersion(self, integer: int) -> None: ...
    def setDataInputCost(self, integer: int) -> None: ...
    def setHeight(self, integer: int) -> None: ...
    def setId(self, integer: int) -> None: ...
    def setInputCost(self, integer: int) -> None: ...
    def setMaxBlockCost(self, integer: int) -> None: ...
    def setMaxBlockSize(self, integer: int) -> None: ...
    def setMinValuePerByte(self, integer: int) -> None: ...
    def setOutputCost(self, integer: int) -> None: ...
    def setStorageFeeFactor(self, integer: int) -> None: ...
    def setTokenAccessCost(self, integer: int) -> None: ...
    def storageFeeFactor(self, integer: int) -> 'EpochParameters': ...
    def toString(self) -> str: ...
    def tokenAccessCost(self, integer: int) -> 'EpochParameters': ...

class Fields(java.util.HashMap[str, str]):
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class FullBlockInfo:
    def __init__(self): ...
    def adProofs(self, string: str) -> 'FullBlockInfo': ...
    def addBlockTransactionsItem(self, transactionInfo1: 'TransactionInfo1') -> 'FullBlockInfo': ...
    def blockTransactions(self, list: java.util.List['TransactionInfo1']) -> 'FullBlockInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def extension(self, blockExtensionInfo: BlockExtensionInfo) -> 'FullBlockInfo': ...
    def getAdProofs(self) -> str: ...
    def getBlockTransactions(self) -> java.util.List['TransactionInfo1']: ...
    def getExtension(self) -> BlockExtensionInfo: ...
    def getHeader(self) -> 'HeaderInfo': ...
    def hashCode(self) -> int: ...
    def header(self, headerInfo: 'HeaderInfo') -> 'FullBlockInfo': ...
    def setAdProofs(self, string: str) -> None: ...
    def setBlockTransactions(self, list: java.util.List['TransactionInfo1']) -> None: ...
    def setExtension(self, blockExtensionInfo: BlockExtensionInfo) -> None: ...
    def setHeader(self, headerInfo: 'HeaderInfo') -> None: ...
    def toString(self) -> str: ...

class HeaderInfo:
    def __init__(self): ...
    def adProofsRoot(self, string: str) -> 'HeaderInfo': ...
    def difficulty(self, string: str) -> 'HeaderInfo': ...
    def epoch(self, integer: int) -> 'HeaderInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def extensionHash(self, string: str) -> 'HeaderInfo': ...
    def getAdProofsRoot(self) -> str: ...
    def getDifficulty(self) -> str: ...
    def getEpoch(self) -> int: ...
    def getExtensionHash(self) -> str: ...
    def getHeight(self) -> int: ...
    def getId(self) -> str: ...
    def getNBits(self) -> int: ...
    def getParentId(self) -> str: ...
    def getPowSolutions(self) -> 'PowSolutionInfo': ...
    def getSize(self) -> int: ...
    def getStateRoot(self) -> str: ...
    def getTimestamp(self) -> int: ...
    def getTransactionsRoot(self) -> str: ...
    def getVersion(self) -> int: ...
    def getVotes(self) -> java.util.List[int]: ...
    def hashCode(self) -> int: ...
    def height(self, integer: int) -> 'HeaderInfo': ...
    def id(self, string: str) -> 'HeaderInfo': ...
    def nBits(self, long: int) -> 'HeaderInfo': ...
    def parentId(self, string: str) -> 'HeaderInfo': ...
    def powSolutions(self, powSolutionInfo: 'PowSolutionInfo') -> 'HeaderInfo': ...
    def setAdProofsRoot(self, string: str) -> None: ...
    def setDifficulty(self, string: str) -> None: ...
    def setEpoch(self, integer: int) -> None: ...
    def setExtensionHash(self, string: str) -> None: ...
    def setHeight(self, integer: int) -> None: ...
    def setId(self, string: str) -> None: ...
    def setNBits(self, long: int) -> None: ...
    def setParentId(self, string: str) -> None: ...
    def setPowSolutions(self, powSolutionInfo: 'PowSolutionInfo') -> None: ...
    def setSize(self, integer: int) -> None: ...
    def setStateRoot(self, string: str) -> None: ...
    def setTimestamp(self, long: int) -> None: ...
    def setTransactionsRoot(self, string: str) -> None: ...
    def setVersion(self, integer: int) -> None: ...
    def setVotes(self, list: java.util.List[int]) -> None: ...
    def size(self, integer: int) -> 'HeaderInfo': ...
    def stateRoot(self, string: str) -> 'HeaderInfo': ...
    def timestamp(self, long: int) -> 'HeaderInfo': ...
    def toString(self) -> str: ...
    def transactionsRoot(self, string: str) -> 'HeaderInfo': ...
    def version(self, integer: int) -> 'HeaderInfo': ...
    def votes(self, list: java.util.List[int]) -> 'HeaderInfo': ...

class InputInfo:
    def __init__(self): ...
    def addAssetsItem(self, assetInstanceInfo: AssetInstanceInfo) -> 'InputInfo': ...
    def additionalRegisters(self, additionalRegisters: AdditionalRegisters) -> 'InputInfo': ...
    def address(self, string: str) -> 'InputInfo': ...
    def assets(self, list: java.util.List[AssetInstanceInfo]) -> 'InputInfo': ...
    def boxId(self, string: str) -> 'InputInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def ergoTree(self, string: str) -> 'InputInfo': ...
    def getAdditionalRegisters(self) -> AdditionalRegisters: ...
    def getAddress(self) -> str: ...
    def getAssets(self) -> java.util.List[AssetInstanceInfo]: ...
    def getBoxId(self) -> str: ...
    def getErgoTree(self) -> str: ...
    def getIndex(self) -> int: ...
    def getOutputBlockId(self) -> str: ...
    def getOutputIndex(self) -> int: ...
    def getOutputTransactionId(self) -> str: ...
    def getSpendingProof(self) -> str: ...
    def getValue(self) -> int: ...
    def hashCode(self) -> int: ...
    def index(self, integer: int) -> 'InputInfo': ...
    def outputBlockId(self, string: str) -> 'InputInfo': ...
    def outputIndex(self, integer: int) -> 'InputInfo': ...
    def outputTransactionId(self, string: str) -> 'InputInfo': ...
    def setAdditionalRegisters(self, additionalRegisters: AdditionalRegisters) -> None: ...
    def setAddress(self, string: str) -> None: ...
    def setAssets(self, list: java.util.List[AssetInstanceInfo]) -> None: ...
    def setBoxId(self, string: str) -> None: ...
    def setErgoTree(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setOutputBlockId(self, string: str) -> None: ...
    def setOutputIndex(self, integer: int) -> None: ...
    def setOutputTransactionId(self, string: str) -> None: ...
    def setSpendingProof(self, string: str) -> None: ...
    def setValue(self, long: int) -> None: ...
    def spendingProof(self, string: str) -> 'InputInfo': ...
    def toString(self) -> str: ...
    def value(self, long: int) -> 'InputInfo': ...

class InputInfo1:
    def __init__(self): ...
    def address(self, string: str) -> 'InputInfo1': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAddress(self) -> str: ...
    def getId(self) -> str: ...
    def getIndex(self) -> int: ...
    def getOutputIndex(self) -> int: ...
    def getOutputTransactionId(self) -> str: ...
    def getSpendingProof(self) -> str: ...
    def getTransactionId(self) -> str: ...
    def getValue(self) -> int: ...
    def hashCode(self) -> int: ...
    def id(self, string: str) -> 'InputInfo1': ...
    def index(self, integer: int) -> 'InputInfo1': ...
    def outputIndex(self, integer: int) -> 'InputInfo1': ...
    def outputTransactionId(self, string: str) -> 'InputInfo1': ...
    def setAddress(self, string: str) -> None: ...
    def setId(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setOutputIndex(self, integer: int) -> None: ...
    def setOutputTransactionId(self, string: str) -> None: ...
    def setSpendingProof(self, string: str) -> None: ...
    def setTransactionId(self, string: str) -> None: ...
    def setValue(self, long: int) -> None: ...
    def spendingProof(self, string: str) -> 'InputInfo1': ...
    def toString(self) -> str: ...
    def transactionId(self, string: str) -> 'InputInfo1': ...
    def value(self, long: int) -> 'InputInfo1': ...

_Items__T = typing.TypeVar('_Items__T')  # <T>
class Items(typing.Generic[_Items__T]):
    def __init__(self): ...
    def addItemsItem(self, t: _Items__T) -> 'Items': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getItems(self) -> java.util.List[_Items__T]: ...
    def getTotal(self) -> int: ...
    def hashCode(self) -> int: ...
    def items(self, list: java.util.List[_Items__T]) -> 'Items': ...
    def setItems(self, list: java.util.List[_Items__T]) -> None: ...
    def setTotal(self, integer: int) -> None: ...
    def toString(self) -> str: ...
    def total(self, integer: int) -> 'Items': ...

class MapV(java.util.HashMap[str, str]):
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class MinerInfo:
    def __init__(self): ...
    def address(self, string: str) -> 'MinerInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAddress(self) -> str: ...
    def getName(self) -> str: ...
    def hashCode(self) -> int: ...
    def name(self, string: str) -> 'MinerInfo': ...
    def setAddress(self, string: str) -> None: ...
    def setName(self, string: str) -> None: ...
    def toString(self) -> str: ...

class NotFound:
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def getReason(self) -> str: ...
    def getStatus(self) -> int: ...
    def hashCode(self) -> int: ...
    def reason(self, string: str) -> 'NotFound': ...
    def setReason(self, string: str) -> None: ...
    def setStatus(self, integer: int) -> None: ...
    def status(self, integer: int) -> 'NotFound': ...
    def toString(self) -> str: ...

class OneOfListOutputInfo: ...

class OutputInfo:
    def __init__(self): ...
    def addAssetsItem(self, assetInstanceInfo: AssetInstanceInfo) -> 'OutputInfo': ...
    def additionalRegisters(self, additionalRegisters: AdditionalRegisters) -> 'OutputInfo': ...
    def address(self, string: str) -> 'OutputInfo': ...
    def assets(self, list: java.util.List[AssetInstanceInfo]) -> 'OutputInfo': ...
    def blockId(self, string: str) -> 'OutputInfo': ...
    def boxId(self, string: str) -> 'OutputInfo': ...
    def creationHeight(self, integer: int) -> 'OutputInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def ergoTree(self, string: str) -> 'OutputInfo': ...
    def getAdditionalRegisters(self) -> AdditionalRegisters: ...
    def getAddress(self) -> str: ...
    def getAssets(self) -> java.util.List[AssetInstanceInfo]: ...
    def getBlockId(self) -> str: ...
    def getBoxId(self) -> str: ...
    def getCreationHeight(self) -> int: ...
    def getErgoTree(self) -> str: ...
    def getIndex(self) -> int: ...
    def getSettlementHeight(self) -> int: ...
    def getSpentTransactionId(self) -> str: ...
    def getTransactionId(self) -> str: ...
    def getValue(self) -> int: ...
    def hashCode(self) -> int: ...
    def index(self, integer: int) -> 'OutputInfo': ...
    def isMainChain(self) -> bool: ...
    def mainChain(self, boolean: bool) -> 'OutputInfo': ...
    def setAdditionalRegisters(self, additionalRegisters: AdditionalRegisters) -> None: ...
    def setAddress(self, string: str) -> None: ...
    def setAssets(self, list: java.util.List[AssetInstanceInfo]) -> None: ...
    def setBlockId(self, string: str) -> None: ...
    def setBoxId(self, string: str) -> None: ...
    def setCreationHeight(self, integer: int) -> None: ...
    def setErgoTree(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setMainChain(self, boolean: bool) -> None: ...
    def setSettlementHeight(self, integer: int) -> None: ...
    def setSpentTransactionId(self, string: str) -> None: ...
    def setTransactionId(self, string: str) -> None: ...
    def setValue(self, long: int) -> None: ...
    def settlementHeight(self, integer: int) -> 'OutputInfo': ...
    def spentTransactionId(self, string: str) -> 'OutputInfo': ...
    def toString(self) -> str: ...
    def transactionId(self, string: str) -> 'OutputInfo': ...
    def value(self, long: int) -> 'OutputInfo': ...

class OutputInfo1:
    def __init__(self): ...
    def addAssetsItem(self, assetInstanceInfo: AssetInstanceInfo) -> 'OutputInfo1': ...
    def additionalRegisters(self, additionalRegisters1: AdditionalRegisters1) -> 'OutputInfo1': ...
    def address(self, string: str) -> 'OutputInfo1': ...
    def assets(self, list: java.util.List[AssetInstanceInfo]) -> 'OutputInfo1': ...
    def creationHeight(self, integer: int) -> 'OutputInfo1': ...
    def equals(self, object: typing.Any) -> bool: ...
    def ergoTree(self, string: str) -> 'OutputInfo1': ...
    def getAdditionalRegisters(self) -> AdditionalRegisters1: ...
    def getAddress(self) -> str: ...
    def getAssets(self) -> java.util.List[AssetInstanceInfo]: ...
    def getCreationHeight(self) -> int: ...
    def getErgoTree(self) -> str: ...
    def getId(self) -> str: ...
    def getIndex(self) -> int: ...
    def getSpentTransactionId(self) -> str: ...
    def getTxId(self) -> str: ...
    def getValue(self) -> int: ...
    def hashCode(self) -> int: ...
    def id(self, string: str) -> 'OutputInfo1': ...
    def index(self, integer: int) -> 'OutputInfo1': ...
    def isMainChain(self) -> bool: ...
    def mainChain(self, boolean: bool) -> 'OutputInfo1': ...
    def setAdditionalRegisters(self, additionalRegisters1: AdditionalRegisters1) -> None: ...
    def setAddress(self, string: str) -> None: ...
    def setAssets(self, list: java.util.List[AssetInstanceInfo]) -> None: ...
    def setCreationHeight(self, integer: int) -> None: ...
    def setErgoTree(self, string: str) -> None: ...
    def setId(self, string: str) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setMainChain(self, boolean: bool) -> None: ...
    def setSpentTransactionId(self, string: str) -> None: ...
    def setTxId(self, string: str) -> None: ...
    def setValue(self, long: int) -> None: ...
    def spentTransactionId(self, string: str) -> 'OutputInfo1': ...
    def toString(self) -> str: ...
    def txId(self, string: str) -> 'OutputInfo1': ...
    def value(self, long: int) -> 'OutputInfo1': ...

class PowSolutionInfo:
    def __init__(self): ...
    def d(self, string: str) -> 'PowSolutionInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getD(self) -> str: ...
    def getN(self) -> str: ...
    def getPk(self) -> str: ...
    def getW(self) -> str: ...
    def hashCode(self) -> int: ...
    def n(self, string: str) -> 'PowSolutionInfo': ...
    def pk(self, string: str) -> 'PowSolutionInfo': ...
    def setD(self, string: str) -> None: ...
    def setN(self, string: str) -> None: ...
    def setPk(self, string: str) -> None: ...
    def setW(self, string: str) -> None: ...
    def toString(self) -> str: ...
    def w(self, string: str) -> 'PowSolutionInfo': ...

class TokenAmount:
    def __init__(self): ...
    def amount(self, long: int) -> 'TokenAmount': ...
    def decimals(self, integer: int) -> 'TokenAmount': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAmount(self) -> int: ...
    def getDecimals(self) -> int: ...
    def getName(self) -> str: ...
    def getTokenId(self) -> str: ...
    def hashCode(self) -> int: ...
    def name(self, string: str) -> 'TokenAmount': ...
    def setAmount(self, long: int) -> None: ...
    def setDecimals(self, integer: int) -> None: ...
    def setName(self, string: str) -> None: ...
    def setTokenId(self, string: str) -> None: ...
    def toString(self) -> str: ...
    def tokenId(self, string: str) -> 'TokenAmount': ...

class TokenInfo:
    def __init__(self): ...
    def boxId(self, string: str) -> 'TokenInfo': ...
    def decimals(self, integer: int) -> 'TokenInfo': ...
    def description(self, string: str) -> 'TokenInfo': ...
    def emissionAmount(self, long: int) -> 'TokenInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getBoxId(self) -> str: ...
    def getDecimals(self) -> int: ...
    def getDescription(self) -> str: ...
    def getEmissionAmount(self) -> int: ...
    def getId(self) -> str: ...
    def getName(self) -> str: ...
    def getType(self) -> str: ...
    def hashCode(self) -> int: ...
    def id(self, string: str) -> 'TokenInfo': ...
    def name(self, string: str) -> 'TokenInfo': ...
    def setBoxId(self, string: str) -> None: ...
    def setDecimals(self, integer: int) -> None: ...
    def setDescription(self, string: str) -> None: ...
    def setEmissionAmount(self, long: int) -> None: ...
    def setId(self, string: str) -> None: ...
    def setName(self, string: str) -> None: ...
    def setType(self, string: str) -> None: ...
    def toString(self) -> str: ...
    def type(self, string: str) -> 'TokenInfo': ...

class TotalBalance:
    def __init__(self): ...
    def confirmed(self, balance: Balance) -> 'TotalBalance': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getConfirmed(self) -> Balance: ...
    def getUnconfirmed(self) -> Balance: ...
    def hashCode(self) -> int: ...
    def setConfirmed(self, balance: Balance) -> None: ...
    def setUnconfirmed(self, balance: Balance) -> None: ...
    def toString(self) -> str: ...
    def unconfirmed(self, balance: Balance) -> 'TotalBalance': ...

class TransactionInfo:
    def __init__(self): ...
    def addDataInputsItem(self, dataInputInfo: DataInputInfo) -> 'TransactionInfo': ...
    def addInputsItem(self, inputInfo: InputInfo) -> 'TransactionInfo': ...
    def addOutputsItem(self, outputInfo: OutputInfo) -> 'TransactionInfo': ...
    def blockId(self, string: str) -> 'TransactionInfo': ...
    def dataInputs(self, list: java.util.List[DataInputInfo]) -> 'TransactionInfo': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getBlockId(self) -> str: ...
    def getDataInputs(self) -> java.util.List[DataInputInfo]: ...
    def getId(self) -> str: ...
    def getInclusionHeight(self) -> int: ...
    def getIndex(self) -> int: ...
    def getInputs(self) -> java.util.List[InputInfo]: ...
    def getNumConfirmations(self) -> int: ...
    def getOutputs(self) -> java.util.List[OutputInfo]: ...
    def getSize(self) -> int: ...
    def getTimestamp(self) -> int: ...
    def hashCode(self) -> int: ...
    def id(self, string: str) -> 'TransactionInfo': ...
    def inclusionHeight(self, integer: int) -> 'TransactionInfo': ...
    def index(self, integer: int) -> 'TransactionInfo': ...
    def inputs(self, list: java.util.List[InputInfo]) -> 'TransactionInfo': ...
    def numConfirmations(self, integer: int) -> 'TransactionInfo': ...
    def outputs(self, list: java.util.List[OutputInfo]) -> 'TransactionInfo': ...
    def setBlockId(self, string: str) -> None: ...
    def setDataInputs(self, list: java.util.List[DataInputInfo]) -> None: ...
    def setId(self, string: str) -> None: ...
    def setInclusionHeight(self, integer: int) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setInputs(self, list: java.util.List[InputInfo]) -> None: ...
    def setNumConfirmations(self, integer: int) -> None: ...
    def setOutputs(self, list: java.util.List[OutputInfo]) -> None: ...
    def setSize(self, integer: int) -> None: ...
    def setTimestamp(self, long: int) -> None: ...
    def size(self, integer: int) -> 'TransactionInfo': ...
    def timestamp(self, long: int) -> 'TransactionInfo': ...
    def toString(self) -> str: ...

class TransactionInfo1:
    def __init__(self): ...
    def addDataInputsItem(self, dataInputInfo1: DataInputInfo1) -> 'TransactionInfo1': ...
    def addInputsItem(self, inputInfo1: InputInfo1) -> 'TransactionInfo1': ...
    def addOutputsItem(self, outputInfo1: OutputInfo1) -> 'TransactionInfo1': ...
    def confirmationsCount(self, integer: int) -> 'TransactionInfo1': ...
    def dataInputs(self, list: java.util.List[DataInputInfo1]) -> 'TransactionInfo1': ...
    def equals(self, object: typing.Any) -> bool: ...
    def getConfirmationsCount(self) -> int: ...
    def getDataInputs(self) -> java.util.List[DataInputInfo1]: ...
    def getHeaderId(self) -> str: ...
    def getId(self) -> str: ...
    def getInclusionHeight(self) -> int: ...
    def getIndex(self) -> int: ...
    def getInputs(self) -> java.util.List[InputInfo1]: ...
    def getOutputs(self) -> java.util.List[OutputInfo1]: ...
    def getTimestamp(self) -> int: ...
    def hashCode(self) -> int: ...
    def headerId(self, string: str) -> 'TransactionInfo1': ...
    def id(self, string: str) -> 'TransactionInfo1': ...
    def inclusionHeight(self, integer: int) -> 'TransactionInfo1': ...
    def index(self, integer: int) -> 'TransactionInfo1': ...
    def inputs(self, list: java.util.List[InputInfo1]) -> 'TransactionInfo1': ...
    def outputs(self, list: java.util.List[OutputInfo1]) -> 'TransactionInfo1': ...
    def setConfirmationsCount(self, integer: int) -> None: ...
    def setDataInputs(self, list: java.util.List[DataInputInfo1]) -> None: ...
    def setHeaderId(self, string: str) -> None: ...
    def setId(self, string: str) -> None: ...
    def setInclusionHeight(self, integer: int) -> None: ...
    def setIndex(self, integer: int) -> None: ...
    def setInputs(self, list: java.util.List[InputInfo1]) -> None: ...
    def setOutputs(self, list: java.util.List[OutputInfo1]) -> None: ...
    def setTimestamp(self, long: int) -> None: ...
    def timestamp(self, long: int) -> 'TransactionInfo1': ...
    def toString(self) -> str: ...

class UnknownErr:
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def getReason(self) -> str: ...
    def getStatus(self) -> int: ...
    def hashCode(self) -> int: ...
    def reason(self, string: str) -> 'UnknownErr': ...
    def setReason(self, string: str) -> None: ...
    def setStatus(self, integer: int) -> None: ...
    def status(self, integer: int) -> 'UnknownErr': ...
    def toString(self) -> str: ...

class ItemsA(Items[OutputInfo]):
    def __init__(self): ...

class ListOutputInfo(OneOfListOutputInfo):
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class Nil(OneOfListOutputInfo):
    def __init__(self): ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("org.ergoplatform.explorer.client.model")``.

    AdditionalRegister: typing.Type[AdditionalRegister]
    AdditionalRegisters: typing.Type[AdditionalRegisters]
    AdditionalRegisters1: typing.Type[AdditionalRegisters1]
    AssetInfo: typing.Type[AssetInfo]
    AssetInstanceInfo: typing.Type[AssetInstanceInfo]
    BadRequest: typing.Type[BadRequest]
    Balance: typing.Type[Balance]
    BlockExtensionInfo: typing.Type[BlockExtensionInfo]
    BlockInfo: typing.Type[BlockInfo]
    BlockReferencesInfo: typing.Type[BlockReferencesInfo]
    BlockSummary: typing.Type[BlockSummary]
    BoxQuery: typing.Type[BoxQuery]
    DataInputInfo: typing.Type[DataInputInfo]
    DataInputInfo1: typing.Type[DataInputInfo1]
    EpochParameters: typing.Type[EpochParameters]
    Fields: typing.Type[Fields]
    FullBlockInfo: typing.Type[FullBlockInfo]
    HeaderInfo: typing.Type[HeaderInfo]
    InputInfo: typing.Type[InputInfo]
    InputInfo1: typing.Type[InputInfo1]
    Items: typing.Type[Items]
    ItemsA: typing.Type[ItemsA]
    ListOutputInfo: typing.Type[ListOutputInfo]
    MapV: typing.Type[MapV]
    MinerInfo: typing.Type[MinerInfo]
    Nil: typing.Type[Nil]
    NotFound: typing.Type[NotFound]
    OneOfListOutputInfo: typing.Type[OneOfListOutputInfo]
    OutputInfo: typing.Type[OutputInfo]
    OutputInfo1: typing.Type[OutputInfo1]
    PowSolutionInfo: typing.Type[PowSolutionInfo]
    TokenAmount: typing.Type[TokenAmount]
    TokenInfo: typing.Type[TokenInfo]
    TotalBalance: typing.Type[TotalBalance]
    TransactionInfo: typing.Type[TransactionInfo]
    TransactionInfo1: typing.Type[TransactionInfo1]
    UnknownErr: typing.Type[UnknownErr]
