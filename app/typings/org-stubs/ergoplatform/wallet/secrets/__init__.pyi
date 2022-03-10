import cats.data
import io.circe
import java.io
import jpype.protocol
import org.ergoplatform.wallet.interface4j
import org.ergoplatform.wallet.settings
import scala
import scala.collection
import scala.collection.immutable
import scala.runtime
import scala.util
import scorex.util.serialization
import sigmastate.basics
import typing



class DerivationPath(scala.Product, scala.Serializable):
    def __init__(self, decodedPath: scala.collection.Seq[typing.Any], publicBranch: bool): ...
    @staticmethod
    def MasterPath() -> 'DerivationPath': ...
    @staticmethod
    def PrivateBranchMasterId() -> str: ...
    @staticmethod
    def PublicBranchMasterId() -> str: ...
    @staticmethod
    def apply(decodedPath: scala.collection.Seq[typing.Any], publicBranch: bool) -> 'DerivationPath': ...
    def bytes(self) -> typing.List[int]: ...
    def canEqual(self, x$1: typing.Any) -> bool: ...
    def copy(self, decodedPath: scala.collection.Seq[typing.Any], publicBranch: bool) -> 'DerivationPath': ...
    def copy$default$1(self) -> scala.collection.Seq[typing.Any]: ...
    def copy$default$2(self) -> bool: ...
    def decodedPath(self) -> scala.collection.Seq[typing.Any]: ...
    def depth(self) -> int: ...
    def encoded(self) -> str: ...
    def equals(self, x$1: typing.Any) -> bool: ...
    def extended(self, idx: int) -> 'DerivationPath': ...
    @staticmethod
    def fromEncoded(path: str) -> scala.util.Try['DerivationPath']: ...
    def hashCode(self) -> int: ...
    def increased(self) -> 'DerivationPath': ...
    def index(self) -> int: ...
    def isEip3(self) -> bool: ...
    def isMaster(self) -> bool: ...
    @staticmethod
    def nextPath(secrets: scala.collection.IndexedSeq['ExtendedSecretKey'], usePreEip3Derivation: bool) -> scala.util.Try['DerivationPath']: ...
    def productArity(self) -> int: ...
    def productElement(self, x$1: int) -> typing.Any: ...
    def productIterator(self) -> scala.collection.Iterator[typing.Any]: ...
    def productPrefix(self) -> str: ...
    def publicBranch(self) -> bool: ...
    def toPrivateBranch(self) -> 'DerivationPath': ...
    def toPublicBranch(self) -> 'DerivationPath': ...
    def toString(self) -> str: ...
    @staticmethod
    def unapply(x$0: 'DerivationPath') -> scala.Option[scala.Tuple2[scala.collection.Seq[typing.Any], typing.Any]]: ...

class DerivationPathSerializer:
    @staticmethod
    def parse(r: scorex.util.serialization.Reader) -> DerivationPath: ...
    @staticmethod
    def parseBytes(bytes: typing.List[int]) -> typing.Any: ...
    @staticmethod
    def parseBytesTry(bytes: typing.List[int]) -> scala.util.Try[DerivationPath]: ...
    @staticmethod
    def parseTry(r: scorex.util.serialization.Reader) -> scala.util.Try[DerivationPath]: ...
    @staticmethod
    def serialize(obj: DerivationPath, w: scorex.util.serialization.Writer) -> None: ...
    @staticmethod
    def toBytes(obj: typing.Any) -> typing.List[int]: ...

class EncryptedSecret(scala.Product, scala.Serializable):
    def __init__(self, cipherText: str, salt: str, iv: str, authTag: str, cipherParams: org.ergoplatform.wallet.settings.EncryptionSettings): ...
    @typing.overload
    @staticmethod
    def apply(cipherText: typing.List[int], salt: typing.List[int], iv: typing.List[int], authTag: typing.List[int], cipherParams: org.ergoplatform.wallet.settings.EncryptionSettings) -> 'EncryptedSecret': ...
    @typing.overload
    @staticmethod
    def apply(cipherText: str, salt: str, iv: str, authTag: str, cipherParams: org.ergoplatform.wallet.settings.EncryptionSettings) -> 'EncryptedSecret': ...
    def authTag(self) -> str: ...
    def canEqual(self, x$1: typing.Any) -> bool: ...
    def cipherParams(self) -> org.ergoplatform.wallet.settings.EncryptionSettings: ...
    def cipherText(self) -> str: ...
    def copy(self, cipherText: str, salt: str, iv: str, authTag: str, cipherParams: org.ergoplatform.wallet.settings.EncryptionSettings) -> 'EncryptedSecret': ...
    def copy$default$1(self) -> str: ...
    def copy$default$2(self) -> str: ...
    def copy$default$3(self) -> str: ...
    def copy$default$4(self) -> str: ...
    def copy$default$5(self) -> org.ergoplatform.wallet.settings.EncryptionSettings: ...
    def equals(self, x$1: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def iv(self) -> str: ...
    def productArity(self) -> int: ...
    def productElement(self, x$1: int) -> typing.Any: ...
    def productIterator(self) -> scala.collection.Iterator[typing.Any]: ...
    def productPrefix(self) -> str: ...
    def salt(self) -> str: ...
    def toString(self) -> str: ...
    @staticmethod
    def unapply(x$0: 'EncryptedSecret') -> scala.Option[scala.Tuple5[str, str, str, str, org.ergoplatform.wallet.settings.EncryptionSettings]]: ...
    class EncryptedSecretDecoder$(io.circe.Decoder['EncryptedSecret']):
        MODULE$: typing.ClassVar['EncryptedSecret.EncryptedSecretDecoder.'] = ...
        def __init__(self): ...
        def accumulating(self, c: io.circe.HCursor) -> cats.data.Validated[cats.data.NonEmptyList[io.circe.DecodingFailure], 'EncryptedSecret']: ...
        def apply(self, cursor: io.circe.HCursor) -> scala.util.Either[io.circe.DecodingFailure, 'EncryptedSecret']: ...
        def at(self, field: str) -> io.circe.Decoder['EncryptedSecret']: ...
        def decodeAccumulating(self, c: io.circe.HCursor) -> cats.data.Validated[cats.data.NonEmptyList[io.circe.DecodingFailure], 'EncryptedSecret']: ...
        def decodeJson(self, j: io.circe.Json) -> scala.util.Either[io.circe.DecodingFailure, 'EncryptedSecret']: ...
        _either__B = typing.TypeVar('_either__B')  # <B>
        def either(self, decodeB: io.circe.Decoder[_either__B]) -> io.circe.Decoder[scala.util.Either['EncryptedSecret', _either__B]]: ...
        _emap__B = typing.TypeVar('_emap__B')  # <B>
        def emap(self, f: scala.Function1['EncryptedSecret', scala.util.Either[str, _emap__B]]) -> io.circe.Decoder[_emap__B]: ...
        _emapTry__B = typing.TypeVar('_emapTry__B')  # <B>
        def emapTry(self, f: scala.Function1['EncryptedSecret', scala.util.Try[_emapTry__B]]) -> io.circe.Decoder[_emapTry__B]: ...
        @typing.overload
        def ensure(self, errors: scala.Function1['EncryptedSecret', scala.collection.immutable.List[str]]) -> io.circe.Decoder['EncryptedSecret']: ...
        @typing.overload
        def ensure(self, pred: scala.Function1['EncryptedSecret', typing.Any], message: scala.Function0[str]) -> io.circe.Decoder['EncryptedSecret']: ...
        _flatMap__B = typing.TypeVar('_flatMap__B')  # <B>
        def flatMap(self, f: scala.Function1['EncryptedSecret', io.circe.Decoder[_flatMap__B]]) -> io.circe.Decoder[_flatMap__B]: ...
        def handleErrorWith(self, f: scala.Function1[io.circe.DecodingFailure, io.circe.Decoder['EncryptedSecret']]) -> io.circe.Decoder['EncryptedSecret']: ...
        def kleisli(self) -> cats.data.Kleisli[scala.util.Either, io.circe.HCursor, 'EncryptedSecret']: ...
        _map__B = typing.TypeVar('_map__B')  # <B>
        def map(self, f: scala.Function1['EncryptedSecret', _map__B]) -> io.circe.Decoder[_map__B]: ...
        def prepare(self, f: scala.Function1[io.circe.ACursor, io.circe.ACursor]) -> io.circe.Decoder['EncryptedSecret']: ...
        _product__B = typing.TypeVar('_product__B')  # <B>
        def product(self, fb: io.circe.Decoder[_product__B]) -> io.circe.Decoder[scala.Tuple2['EncryptedSecret', _product__B]]: ...
        def tryDecode(self, c: io.circe.ACursor) -> scala.util.Either[io.circe.DecodingFailure, 'EncryptedSecret']: ...
        def tryDecodeAccumulating(self, c: io.circe.ACursor) -> cats.data.Validated[cats.data.NonEmptyList[io.circe.DecodingFailure], 'EncryptedSecret']: ...
        @typing.overload
        def validate(self, errors: scala.Function1[io.circe.HCursor, scala.collection.immutable.List[str]]) -> io.circe.Decoder['EncryptedSecret']: ...
        @typing.overload
        def validate(self, pred: scala.Function1[io.circe.HCursor, typing.Any], message: scala.Function0[str]) -> io.circe.Decoder['EncryptedSecret']: ...
        def withErrorMessage(self, message: str) -> io.circe.Decoder['EncryptedSecret']: ...
    class EncryptedSecretEncoder$(io.circe.Encoder['EncryptedSecret']):
        MODULE$: typing.ClassVar['EncryptedSecret.EncryptedSecretEncoder.'] = ...
        def __init__(self): ...
        def apply(self, secret: 'EncryptedSecret') -> io.circe.Json: ...
        _contramap__B = typing.TypeVar('_contramap__B')  # <B>
        def contramap(self, f: scala.Function1[_contramap__B, 'EncryptedSecret']) -> io.circe.Encoder[_contramap__B]: ...
        def mapJson(self, f: scala.Function1[io.circe.Json, io.circe.Json]) -> io.circe.Encoder['EncryptedSecret']: ...

_ExtendedKey__T = typing.TypeVar('_ExtendedKey__T', bound='ExtendedKey')  # <T>
class ExtendedKey(typing.Generic[_ExtendedKey__T]):
    @staticmethod
    def $init$($this: 'ExtendedKey') -> None: ...
    def chainCode(self) -> typing.List[int]: ...
    def child(self, idx: int) -> _ExtendedKey__T: ...
    def derive(self, upPath: DerivationPath) -> _ExtendedKey__T: ...
    def keyBytes(self) -> typing.List[int]: ...
    def path(self) -> DerivationPath: ...
    def selfReflection(self) -> _ExtendedKey__T: ...

class ExtendedPublicKeySerializer:
    @staticmethod
    def PublicKeyBytesSize() -> int: ...
    @staticmethod
    def parse(r: scorex.util.serialization.Reader) -> 'ExtendedPublicKey': ...
    @staticmethod
    def parseBytes(bytes: typing.List[int]) -> typing.Any: ...
    @staticmethod
    def parseBytesTry(bytes: typing.List[int]) -> scala.util.Try['ExtendedPublicKey']: ...
    @staticmethod
    def parseTry(r: scorex.util.serialization.Reader) -> scala.util.Try['ExtendedPublicKey']: ...
    @staticmethod
    def serialize(obj: 'ExtendedPublicKey', w: scorex.util.serialization.Writer) -> None: ...
    @staticmethod
    def toBytes(obj: typing.Any) -> typing.List[int]: ...

class ExtendedSecretKeySerializer:
    @staticmethod
    def parse(r: scorex.util.serialization.Reader) -> 'ExtendedSecretKey': ...
    @staticmethod
    def parseBytes(bytes: typing.List[int]) -> typing.Any: ...
    @staticmethod
    def parseBytesTry(bytes: typing.List[int]) -> scala.util.Try['ExtendedSecretKey']: ...
    @staticmethod
    def parseTry(r: scorex.util.serialization.Reader) -> scala.util.Try['ExtendedSecretKey']: ...
    @staticmethod
    def serialize(obj: 'ExtendedSecretKey', w: scorex.util.serialization.Writer) -> None: ...
    @staticmethod
    def toBytes(obj: typing.Any) -> typing.List[int]: ...

class Index:
    @staticmethod
    def HardRangeStart() -> int: ...
    @staticmethod
    def hardIndex(i: int) -> int: ...
    @staticmethod
    def isHardened(i: int) -> bool: ...
    @staticmethod
    def parseIndex(xs: typing.List[int]) -> int: ...
    @staticmethod
    def serializeIndex(i: int) -> typing.List[int]: ...

class SecretKey:
    def privateInput(self) -> sigmastate.basics.SigmaProtocolPrivateInput[typing.Any, typing.Any]: ...

class SecretStorage:
    def checkSeed(self, mnemonic: org.ergoplatform.wallet.interface4j.SecretString, mnemonicPassOpt: scala.Option[org.ergoplatform.wallet.interface4j.SecretString]) -> bool: ...
    def isLocked(self) -> bool: ...
    def lock(self) -> None: ...
    def secret(self) -> scala.Option['ExtendedSecretKey']: ...
    def secretFile(self) -> java.io.File: ...
    def unlock(self, pass_: org.ergoplatform.wallet.interface4j.SecretString) -> scala.util.Try[scala.runtime.BoxedUnit]: ...

class ExtendedPublicKey(ExtendedKey['ExtendedPublicKey']):
    def __init__(self, keyBytes: typing.List[int], chainCode: typing.List[int], path: DerivationPath): ...
    def chainCode(self) -> typing.List[int]: ...
    def child(self, idx: int) -> 'ExtendedPublicKey': ...
    def derive(self, upPath: DerivationPath) -> ExtendedKey: ...
    @staticmethod
    def deriveChildPublicKey(parentKey: 'ExtendedPublicKey', idx: int) -> 'ExtendedPublicKey': ...
    def equals(self, obj: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def key(self) -> sigmastate.basics.DLogProtocol.ProveDlog: ...
    def keyBytes(self) -> typing.List[int]: ...
    def path(self) -> DerivationPath: ...
    def selfReflection(self) -> 'ExtendedPublicKey': ...
    def toString(self) -> str: ...

class ExtendedSecretKey(ExtendedKey['ExtendedSecretKey'], SecretKey):
    def __init__(self, keyBytes: typing.List[int], chainCode: typing.List[int], path: DerivationPath): ...
    def chainCode(self) -> typing.List[int]: ...
    def child(self, idx: int) -> 'ExtendedSecretKey': ...
    def derive(self, upPath: DerivationPath) -> ExtendedKey: ...
    @staticmethod
    def deriveChildPublicKey(parentKey: 'ExtendedSecretKey', idx: int) -> ExtendedPublicKey: ...
    @staticmethod
    def deriveChildSecretKey(parentKey: 'ExtendedSecretKey', idx: int) -> 'ExtendedSecretKey': ...
    @staticmethod
    def deriveMasterKey(seed: typing.List[int]) -> 'ExtendedSecretKey': ...
    def equals(self, obj: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def isErased(self) -> bool: ...
    def keyBytes(self) -> typing.List[int]: ...
    def path(self) -> DerivationPath: ...
    def privateInput(self) -> sigmastate.basics.DLogProtocol.DLogProverInput: ...
    def publicImage(self) -> sigmastate.basics.DLogProtocol.ProveDlog: ...
    def publicKey(self) -> ExtendedPublicKey: ...
    def selfReflection(self) -> 'ExtendedSecretKey': ...
    def zeroSecret(self) -> None: ...

class JsonSecretStorage(SecretStorage):
    def __init__(self, secretFile: typing.Union[java.io.File, jpype.protocol.SupportsPath], encryptionSettings: org.ergoplatform.wallet.settings.EncryptionSettings): ...
    def checkSeed(self, mnemonic: org.ergoplatform.wallet.interface4j.SecretString, mnemonicPassOpt: scala.Option[org.ergoplatform.wallet.interface4j.SecretString]) -> bool: ...
    @staticmethod
    def init(seed: typing.List[int], pass_: org.ergoplatform.wallet.interface4j.SecretString, settings: org.ergoplatform.wallet.settings.SecretStorageSettings) -> 'JsonSecretStorage': ...
    def isLocked(self) -> bool: ...
    def lock(self) -> None: ...
    @staticmethod
    def readFile(settings: org.ergoplatform.wallet.settings.SecretStorageSettings) -> scala.util.Try['JsonSecretStorage']: ...
    @staticmethod
    def restore(mnemonic: org.ergoplatform.wallet.interface4j.SecretString, mnemonicPassOpt: scala.Option[org.ergoplatform.wallet.interface4j.SecretString], encryptionPass: org.ergoplatform.wallet.interface4j.SecretString, settings: org.ergoplatform.wallet.settings.SecretStorageSettings) -> 'JsonSecretStorage': ...
    def secret(self) -> scala.Option[ExtendedSecretKey]: ...
    def secretFile(self) -> java.io.File: ...
    def unlock(self, pass_: org.ergoplatform.wallet.interface4j.SecretString) -> scala.util.Try[scala.runtime.BoxedUnit]: ...

class PrimitiveSecretKey(SecretKey):
    @staticmethod
    def apply(sigmaPrivateInput: sigmastate.basics.SigmaProtocolPrivateInput[typing.Any, typing.Any]) -> 'PrimitiveSecretKey': ...

class DhtSecretKey(PrimitiveSecretKey, scala.Product, scala.Serializable):
    def __init__(self, privateInput: sigmastate.basics.DiffieHellmanTupleProverInput): ...
    _andThen__A = typing.TypeVar('_andThen__A')  # <A>
    @staticmethod
    def andThen(g: scala.Function1['DhtSecretKey', _andThen__A]) -> scala.Function1[sigmastate.basics.DiffieHellmanTupleProverInput, _andThen__A]: ...
    @staticmethod
    def apply(privateInput: sigmastate.basics.DiffieHellmanTupleProverInput) -> 'DhtSecretKey': ...
    def canEqual(self, x$1: typing.Any) -> bool: ...
    _compose__A = typing.TypeVar('_compose__A')  # <A>
    @staticmethod
    def compose(g: scala.Function1[_compose__A, sigmastate.basics.DiffieHellmanTupleProverInput]) -> scala.Function1[_compose__A, 'DhtSecretKey']: ...
    def copy(self, privateInput: sigmastate.basics.DiffieHellmanTupleProverInput) -> 'DhtSecretKey': ...
    def copy$default$1(self) -> sigmastate.basics.DiffieHellmanTupleProverInput: ...
    def equals(self, x$1: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def privateInput(self) -> sigmastate.basics.DiffieHellmanTupleProverInput: ...
    def productArity(self) -> int: ...
    def productElement(self, x$1: int) -> typing.Any: ...
    def productIterator(self) -> scala.collection.Iterator[typing.Any]: ...
    def productPrefix(self) -> str: ...
    def toString(self) -> str: ...
    @staticmethod
    def unapply(x$0: 'DhtSecretKey') -> scala.Option[sigmastate.basics.DiffieHellmanTupleProverInput]: ...

class DlogSecretKey(PrimitiveSecretKey, scala.Product, scala.Serializable):
    def __init__(self, privateInput: sigmastate.basics.DLogProtocol.DLogProverInput): ...
    _andThen__A = typing.TypeVar('_andThen__A')  # <A>
    @staticmethod
    def andThen(g: scala.Function1['DlogSecretKey', _andThen__A]) -> scala.Function1[sigmastate.basics.DLogProtocol.DLogProverInput, _andThen__A]: ...
    @staticmethod
    def apply(privateInput: sigmastate.basics.DLogProtocol.DLogProverInput) -> 'DlogSecretKey': ...
    def canEqual(self, x$1: typing.Any) -> bool: ...
    _compose__A = typing.TypeVar('_compose__A')  # <A>
    @staticmethod
    def compose(g: scala.Function1[_compose__A, sigmastate.basics.DLogProtocol.DLogProverInput]) -> scala.Function1[_compose__A, 'DlogSecretKey']: ...
    def copy(self, privateInput: sigmastate.basics.DLogProtocol.DLogProverInput) -> 'DlogSecretKey': ...
    def copy$default$1(self) -> sigmastate.basics.DLogProtocol.DLogProverInput: ...
    def equals(self, x$1: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def privateInput(self) -> sigmastate.basics.DLogProtocol.DLogProverInput: ...
    def productArity(self) -> int: ...
    def productElement(self, x$1: int) -> typing.Any: ...
    def productIterator(self) -> scala.collection.Iterator[typing.Any]: ...
    def productPrefix(self) -> str: ...
    def toString(self) -> str: ...
    @staticmethod
    def unapply(x$0: 'DlogSecretKey') -> scala.Option[sigmastate.basics.DLogProtocol.DLogProverInput]: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("org.ergoplatform.wallet.secrets")``.

    DerivationPath: typing.Type[DerivationPath]
    DerivationPathSerializer: typing.Type[DerivationPathSerializer]
    DhtSecretKey: typing.Type[DhtSecretKey]
    DlogSecretKey: typing.Type[DlogSecretKey]
    EncryptedSecret: typing.Type[EncryptedSecret]
    ExtendedKey: typing.Type[ExtendedKey]
    ExtendedPublicKey: typing.Type[ExtendedPublicKey]
    ExtendedPublicKeySerializer: typing.Type[ExtendedPublicKeySerializer]
    ExtendedSecretKey: typing.Type[ExtendedSecretKey]
    ExtendedSecretKeySerializer: typing.Type[ExtendedSecretKeySerializer]
    Index: typing.Type[Index]
    JsonSecretStorage: typing.Type[JsonSecretStorage]
    PrimitiveSecretKey: typing.Type[PrimitiveSecretKey]
    SecretKey: typing.Type[SecretKey]
    SecretStorage: typing.Type[SecretStorage]
