import java.lang.annotation
import java.lang.reflect
import scala
import scala.collection
import scala.collection.immutable
import scala.collection.mutable
import scala.reflect.api
import scala.reflect.io
import scala.reflect.macros
import scala.reflect.runtime
import scala.runtime
import typing



class NameTransformer:
    @staticmethod
    def LAZY_LOCAL_SUFFIX_STRING() -> str: ...
    @staticmethod
    def LOCAL_SUFFIX_STRING() -> str: ...
    @staticmethod
    def MODULE_INSTANCE_NAME() -> str: ...
    @staticmethod
    def MODULE_SUFFIX_STRING() -> str: ...
    @staticmethod
    def MODULE_VAR_SUFFIX_STRING() -> str: ...
    @staticmethod
    def NAME_JOIN_STRING() -> str: ...
    @staticmethod
    def SETTER_SUFFIX_STRING() -> str: ...
    @staticmethod
    def TRAIT_SETTER_SEPARATOR_STRING() -> str: ...
    @staticmethod
    def decode(name0: str) -> str: ...
    @staticmethod
    def encode(name: str) -> str: ...
    class OpCodes:
        def __init__(self, op: str, code: str, next: 'NameTransformer.OpCodes'): ...
        def code(self) -> str: ...
        def next(self) -> 'NameTransformer.OpCodes': ...
        def op(self) -> str: ...

class NoManifest:
    @staticmethod
    def toString() -> str: ...

_OptManifest__T = typing.TypeVar('_OptManifest__T')  # <T>
class OptManifest(scala.Serializable, typing.Generic[_OptManifest__T]): ...

class ScalaLongSignature(java.lang.annotation.Annotation):
    def bytes(self) -> typing.List[str]: ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class ScalaSignature(java.lang.annotation.Annotation):
    def bytes(self) -> str: ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...

class package:
    @staticmethod
    def ClassManifest() -> 'ClassManifestFactory.': ...
    @staticmethod
    def Manifest() -> 'ManifestFactory.': ...
    _classTag__T = typing.TypeVar('_classTag__T')  # <T>
    @staticmethod
    def classTag(ctag: 'ClassTag'[_classTag__T]) -> 'ClassTag'[_classTag__T]: ...
    _ensureAccessible__T = typing.TypeVar('_ensureAccessible__T', bound=java.lang.reflect.AccessibleObject)  # <T>
    @staticmethod
    def ensureAccessible(m: _ensureAccessible__T) -> _ensureAccessible__T: ...

_ClassManifestDeprecatedApis__T = typing.TypeVar('_ClassManifestDeprecatedApis__T')  # <T>
class ClassManifestDeprecatedApis(OptManifest[_ClassManifestDeprecatedApis__T], typing.Generic[_ClassManifestDeprecatedApis__T]):
    def $greater$colon$greater(self, that: 'ClassTag'[typing.Any]) -> bool: ...
    @staticmethod
    def $init$($this: 'ClassManifestDeprecatedApis') -> None: ...
    def $less$colon$less(self, that: 'ClassTag'[typing.Any]) -> bool: ...
    def argString(self) -> str: ...
    _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
    def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
    def arrayManifest(self) -> 'ClassTag'[typing.Any]: ...
    def canEqual(self, other: typing.Any) -> bool: ...
    def erasure(self) -> typing.Type[typing.Any]: ...
    def newArray(self, len: int) -> typing.Any: ...
    def newArray2(self, len: int) -> typing.List[typing.Any]: ...
    def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
    def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
    def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
    def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ClassManifestDeprecatedApis__T]: ...
    def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ClassManifestDeprecatedApis__T]: ...
    def typeArguments(self) -> scala.collection.immutable.List[OptManifest[typing.Any]]: ...

_AnyValManifest__T = typing.TypeVar('_AnyValManifest__T')  # <T>
class AnyValManifest(scala.reflect.Manifest[_AnyValManifest__T], typing.Generic[_AnyValManifest__T]):
    serialVersionUID: typing.ClassVar[int] = ...
    def __init__(self, toString: str): ...
    def $greater$colon$greater(self, that: 'ClassTag'[typing.Any]) -> bool: ...
    def $less$colon$less(self, that: 'ClassTag'[typing.Any]) -> bool: ...
    def argString(self) -> str: ...
    _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
    def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
    def arrayManifest(self) -> 'Manifest'[typing.Any]: ...
    def canEqual(self, other: typing.Any) -> bool: ...
    def equals(self, that: typing.Any) -> bool: ...
    def erasure(self) -> typing.Type[typing.Any]: ...
    def hashCode(self) -> int: ...
    def newArray(self, len: int) -> typing.Any: ...
    def newArray2(self, len: int) -> typing.List[typing.Any]: ...
    def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
    def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
    def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
    def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_AnyValManifest__T]: ...
    def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_AnyValManifest__T]: ...
    def toString(self) -> str: ...
    def typeArguments(self) -> scala.collection.immutable.List['Manifest'[typing.Any]]: ...
    def unapply(self, x: typing.Any) -> scala.Option[_AnyValManifest__T]: ...
    def wrap(self) -> 'ClassTag'[typing.Any]: ...

_ClassManifestFactory__AbstractTypeClassManifest__T = typing.TypeVar('_ClassManifestFactory__AbstractTypeClassManifest__T')  # <T>
class ClassManifestFactory:
    @staticmethod
    def Any() -> 'Manifest'[typing.Any]: ...
    @staticmethod
    def AnyVal() -> 'Manifest'[typing.Any]: ...
    @staticmethod
    def Boolean() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Byte() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Char() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Double() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Float() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Int() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Long() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Nothing() -> 'Manifest'[scala.runtime.Nothing.]: ...
    @staticmethod
    def Null() -> 'Manifest'[scala.runtime.Null.]: ...
    @staticmethod
    def Object() -> 'Manifest'[typing.Any]: ...
    @staticmethod
    def Short() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Unit() -> AnyValManifest[scala.runtime.BoxedUnit]: ...
    _abstractType_0__T = typing.TypeVar('_abstractType_0__T')  # <T>
    _abstractType_1__T = typing.TypeVar('_abstractType_1__T')  # <T>
    @typing.overload
    @staticmethod
    def abstractType(prefix: OptManifest[typing.Any], name: str, clazz: typing.Type[typing.Any], args: scala.collection.Seq[OptManifest[typing.Any]]) -> 'ClassTag'[_abstractType_0__T]: ...
    @typing.overload
    @staticmethod
    def abstractType(prefix: OptManifest[typing.Any], name: str, upperbound: 'ClassTag'[typing.Any], args: scala.collection.Seq[OptManifest[typing.Any]]) -> 'ClassTag'[_abstractType_1__T]: ...
    _arrayType__T = typing.TypeVar('_arrayType__T')  # <T>
    @staticmethod
    def arrayType(arg: OptManifest[typing.Any]) -> 'ClassTag'[typing.Any]: ...
    _classType_0__T = typing.TypeVar('_classType_0__T')  # <T>
    _classType_1__T = typing.TypeVar('_classType_1__T')  # <T>
    _classType_2__T = typing.TypeVar('_classType_2__T')  # <T>
    @typing.overload
    @staticmethod
    def classType(clazz: typing.Type[typing.Any]) -> 'ClassTag'[_classType_0__T]: ...
    @typing.overload
    @staticmethod
    def classType(clazz: typing.Type[typing.Any], arg1: OptManifest[typing.Any], args: scala.collection.Seq[OptManifest[typing.Any]]) -> 'ClassTag'[_classType_1__T]: ...
    @typing.overload
    @staticmethod
    def classType(prefix: OptManifest[typing.Any], clazz: typing.Type[typing.Any], args: scala.collection.Seq[OptManifest[typing.Any]]) -> 'ClassTag'[_classType_2__T]: ...
    _fromClass__T = typing.TypeVar('_fromClass__T')  # <T>
    @staticmethod
    def fromClass(clazz: typing.Type[_fromClass__T]) -> 'ClassTag'[_fromClass__T]: ...
    _singleType__T = typing.TypeVar('_singleType__T')  # <T>
    @staticmethod
    def singleType(value: typing.Any) -> 'Manifest'[_singleType__T]: ...
    class AbstractTypeClassManifest(scala.reflect.ClassTag[_ClassManifestFactory__AbstractTypeClassManifest__T], typing.Generic[_ClassManifestFactory__AbstractTypeClassManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, prefix: OptManifest[typing.Any], name: str, clazz: typing.Type[typing.Any], args: scala.collection.Seq[OptManifest[typing.Any]]): ...
        def $greater$colon$greater(self, that: 'ClassTag'[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: 'ClassTag'[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> 'ClassTag'[typing.Any]: ...
        def canEqual(self, x: typing.Any) -> bool: ...
        def equals(self, x: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ClassManifestFactory__AbstractTypeClassManifest__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ClassManifestFactory__AbstractTypeClassManifest__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[OptManifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ClassManifestFactory__AbstractTypeClassManifest__T]: ...
        def wrap(self) -> 'ClassTag'[typing.Any]: ...
    class : ...

_ClassTag__GenericClassTag__T = typing.TypeVar('_ClassTag__GenericClassTag__T')  # <T>
_ClassTag__T = typing.TypeVar('_ClassTag__T')  # <T>
class ClassTag(ClassManifestDeprecatedApis[_ClassTag__T], scala.Equals, typing.Generic[_ClassTag__T]):
    @staticmethod
    def $init$($this: 'ClassTag') -> None: ...
    @staticmethod
    def Any() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def AnyRef() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def AnyVal() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Boolean() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Byte() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Char() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Double() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Float() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Int() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Long() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Nothing() -> 'ClassTag'[scala.runtime.Nothing.]: ...
    @staticmethod
    def Null() -> 'ClassTag'[scala.runtime.Null.]: ...
    @staticmethod
    def Object() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Short() -> 'ClassTag'[typing.Any]: ...
    @staticmethod
    def Unit() -> 'ClassTag'[scala.runtime.BoxedUnit]: ...
    _apply__T = typing.TypeVar('_apply__T')  # <T>
    @staticmethod
    def apply(runtimeClass1: typing.Type[typing.Any]) -> 'ClassTag'[_apply__T]: ...
    def canEqual(self, x: typing.Any) -> bool: ...
    def equals(self, x: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def newArray(self, len: int) -> typing.Any: ...
    def runtimeClass(self) -> typing.Type[typing.Any]: ...
    def toString(self) -> str: ...
    def unapply(self, x: typing.Any) -> scala.Option[_ClassTag__T]: ...
    def wrap(self) -> 'ClassTag'[typing.Any]: ...
    class GenericClassTag(scala.reflect.ClassTag[_ClassTag__GenericClassTag__T], typing.Generic[_ClassTag__GenericClassTag__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, runtimeClass: typing.Type[typing.Any]): ...
        def $greater$colon$greater(self, that: 'ClassTag'[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: 'ClassTag'[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> 'ClassTag'[typing.Any]: ...
        def canEqual(self, x: typing.Any) -> bool: ...
        def equals(self, x: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ClassTag__GenericClassTag__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ClassTag__GenericClassTag__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[OptManifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ClassTag__GenericClassTag__T]: ...
        def wrap(self) -> 'ClassTag'[typing.Any]: ...

_ClassTypeManifest__T = typing.TypeVar('_ClassTypeManifest__T')  # <T>
class ClassTypeManifest(ClassTag[_ClassTypeManifest__T], typing.Generic[_ClassTypeManifest__T]):
    serialVersionUID: typing.ClassVar[int] = ...
    def __init__(self, prefix: scala.Option[OptManifest[typing.Any]], runtimeClass: typing.Type[typing.Any], typeArguments: scala.collection.immutable.List[OptManifest[typing.Any]]): ...
    def $greater$colon$greater(self, that: ClassTag[typing.Any]) -> bool: ...
    def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
    def argString(self) -> str: ...
    _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
    def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
    def arrayManifest(self) -> ClassTag[typing.Any]: ...
    def canEqual(self, x: typing.Any) -> bool: ...
    def equals(self, x: typing.Any) -> bool: ...
    def erasure(self) -> typing.Type[typing.Any]: ...
    def hashCode(self) -> int: ...
    def newArray(self, len: int) -> typing.Any: ...
    def newArray2(self, len: int) -> typing.List[typing.Any]: ...
    def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
    def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
    def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
    def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ClassTypeManifest__T]: ...
    def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ClassTypeManifest__T]: ...
    def runtimeClass(self) -> typing.Type[typing.Any]: ...
    def toString(self) -> str: ...
    def typeArguments(self) -> scala.collection.immutable.List[OptManifest[typing.Any]]: ...
    def unapply(self, x: typing.Any) -> scala.Option[_ClassTypeManifest__T]: ...
    def wrap(self) -> ClassTag[typing.Any]: ...

_Manifest__T = typing.TypeVar('_Manifest__T')  # <T>
class Manifest(ClassTag[_Manifest__T], typing.Generic[_Manifest__T]):
    @staticmethod
    def $init$($this: 'Manifest') -> None: ...
    @typing.overload
    def arrayManifest(self) -> ClassTag[typing.Any]: ...
    @typing.overload
    def arrayManifest(self) -> 'Manifest'[typing.Any]: ...
    def canEqual(self, that: typing.Any) -> bool: ...
    def equals(self, that: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def toString(self) -> str: ...
    def typeArguments(self) -> scala.collection.immutable.List['Manifest'[typing.Any]]: ...

_ManifestFactory__AbstractTypeManifest__T = typing.TypeVar('_ManifestFactory__AbstractTypeManifest__T')  # <T>
_ManifestFactory__ClassTypeManifest__T = typing.TypeVar('_ManifestFactory__ClassTypeManifest__T')  # <T>
_ManifestFactory__IntersectionTypeManifest__T = typing.TypeVar('_ManifestFactory__IntersectionTypeManifest__T')  # <T>
_ManifestFactory__PhantomManifest__T = typing.TypeVar('_ManifestFactory__PhantomManifest__T')  # <T>
_ManifestFactory__SingletonTypeManifest__T = typing.TypeVar('_ManifestFactory__SingletonTypeManifest__T')  # <T>
_ManifestFactory__WildcardManifest__T = typing.TypeVar('_ManifestFactory__WildcardManifest__T')  # <T>
class ManifestFactory:
    @staticmethod
    def Any() -> Manifest[typing.Any]: ...
    @staticmethod
    def AnyRef() -> Manifest[typing.Any]: ...
    @staticmethod
    def AnyVal() -> Manifest[typing.Any]: ...
    @staticmethod
    def Boolean() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Byte() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Char() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Double() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Float() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Int() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Long() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Nothing() -> Manifest[scala.runtime.Nothing.]: ...
    @staticmethod
    def Null() -> Manifest[scala.runtime.Null.]: ...
    @staticmethod
    def Object() -> Manifest[typing.Any]: ...
    @staticmethod
    def Short() -> AnyValManifest[typing.Any]: ...
    @staticmethod
    def Unit() -> AnyValManifest[scala.runtime.BoxedUnit]: ...
    _abstractType__T = typing.TypeVar('_abstractType__T')  # <T>
    @staticmethod
    def abstractType(prefix: Manifest[typing.Any], name: str, upperBound: typing.Type[typing.Any], args: scala.collection.Seq[Manifest[typing.Any]]) -> Manifest[_abstractType__T]: ...
    _arrayType__T = typing.TypeVar('_arrayType__T')  # <T>
    @staticmethod
    def arrayType(arg: Manifest[typing.Any]) -> Manifest[typing.Any]: ...
    _classType_0__T = typing.TypeVar('_classType_0__T')  # <T>
    _classType_1__T = typing.TypeVar('_classType_1__T')  # <T>
    _classType_2__T = typing.TypeVar('_classType_2__T')  # <T>
    @typing.overload
    @staticmethod
    def classType(clazz: typing.Type[typing.Any]) -> Manifest[_classType_0__T]: ...
    @typing.overload
    @staticmethod
    def classType(clazz: typing.Type[_classType_1__T], arg1: Manifest[typing.Any], args: scala.collection.Seq[Manifest[typing.Any]]) -> Manifest[_classType_1__T]: ...
    @typing.overload
    @staticmethod
    def classType(prefix: Manifest[typing.Any], clazz: typing.Type[typing.Any], args: scala.collection.Seq[Manifest[typing.Any]]) -> Manifest[_classType_2__T]: ...
    _intersectionType__T = typing.TypeVar('_intersectionType__T')  # <T>
    @staticmethod
    def intersectionType(parents: scala.collection.Seq[Manifest[typing.Any]]) -> Manifest[_intersectionType__T]: ...
    _singleType__T = typing.TypeVar('_singleType__T')  # <T>
    @staticmethod
    def singleType(value: typing.Any) -> Manifest[_singleType__T]: ...
    @staticmethod
    def valueManifests() -> scala.collection.immutable.List[AnyValManifest[typing.Any]]: ...
    _wildcardType__T = typing.TypeVar('_wildcardType__T')  # <T>
    @staticmethod
    def wildcardType(lowerBound: Manifest[typing.Any], upperBound: Manifest[typing.Any]) -> Manifest[_wildcardType__T]: ...
    class AbstractTypeManifest(Manifest[_ManifestFactory__AbstractTypeManifest__T], typing.Generic[_ManifestFactory__AbstractTypeManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, prefix: Manifest[typing.Any], name: str, upperBound: typing.Type[typing.Any], args: scala.collection.Seq[Manifest[typing.Any]]): ...
        def $greater$colon$greater(self, that: ClassTag[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> Manifest[typing.Any]: ...
        def canEqual(self, that: typing.Any) -> bool: ...
        def equals(self, that: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ManifestFactory__AbstractTypeManifest__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ManifestFactory__AbstractTypeManifest__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[Manifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ManifestFactory__AbstractTypeManifest__T]: ...
        def wrap(self) -> ClassTag[typing.Any]: ...
    class AnyManifest(scala.reflect.ManifestFactory.PhantomManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def newArray(self, len: int) -> typing.List[typing.Any]: ...
    class AnyValPhantomManifest(scala.reflect.ManifestFactory.PhantomManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def newArray(self, len: int) -> typing.List[typing.Any]: ...
    class BooleanManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[bool]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[bool]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class ByteManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[int]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[int]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class CharManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[str]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[str]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class ClassTypeManifest(Manifest[_ManifestFactory__ClassTypeManifest__T], typing.Generic[_ManifestFactory__ClassTypeManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, prefix: scala.Option[Manifest[typing.Any]], runtimeClass: typing.Type[typing.Any], typeArguments: scala.collection.immutable.List[Manifest[typing.Any]]): ...
        def $greater$colon$greater(self, that: ClassTag[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> Manifest[typing.Any]: ...
        def canEqual(self, that: typing.Any) -> bool: ...
        def equals(self, that: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ManifestFactory__ClassTypeManifest__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ManifestFactory__ClassTypeManifest__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[Manifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ManifestFactory__ClassTypeManifest__T]: ...
        def wrap(self) -> ClassTag[typing.Any]: ...
    class DoubleManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[float]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[float]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class FloatManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[float]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[float]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class IntManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[int]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[int]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class IntersectionTypeManifest(Manifest[_ManifestFactory__IntersectionTypeManifest__T], typing.Generic[_ManifestFactory__IntersectionTypeManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, parents: scala.collection.Seq[Manifest[typing.Any]]): ...
        def $greater$colon$greater(self, that: ClassTag[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> Manifest[typing.Any]: ...
        def canEqual(self, that: typing.Any) -> bool: ...
        def equals(self, that: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ManifestFactory__IntersectionTypeManifest__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ManifestFactory__IntersectionTypeManifest__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[Manifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ManifestFactory__IntersectionTypeManifest__T]: ...
        def wrap(self) -> ClassTag[typing.Any]: ...
    class LongManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[int]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[int]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class NothingManifest(scala.reflect.ManifestFactory.PhantomManifest[scala.runtime.Nothing.]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def newArray(self, len: int) -> typing.List[typing.Any]: ...
    class NullManifest(scala.reflect.ManifestFactory.PhantomManifest[scala.runtime.Null.]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def newArray(self, len: int) -> typing.List[typing.Any]: ...
    class ObjectManifest(scala.reflect.ManifestFactory.PhantomManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def newArray(self, len: int) -> typing.List[typing.Any]: ...
    class PhantomManifest(scala.reflect.ManifestFactory.ClassTypeManifest[_ManifestFactory__PhantomManifest__T], typing.Generic[_ManifestFactory__PhantomManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, _runtimeClass: typing.Type[typing.Any], toString: str): ...
        def equals(self, that: typing.Any) -> bool: ...
        def hashCode(self) -> int: ...
        def toString(self) -> str: ...
    class ShortManifest(AnyValManifest[typing.Any]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        def newArray(self, len: int) -> typing.List[int]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[typing.Any]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[typing.Any]: ...
        def runtimeClass(self) -> typing.Type[int]: ...
        def unapply(self, x: typing.Any) -> scala.Option[typing.Any]: ...
    class SingletonTypeManifest(Manifest[_ManifestFactory__SingletonTypeManifest__T], typing.Generic[_ManifestFactory__SingletonTypeManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, value: typing.Any): ...
        def $greater$colon$greater(self, that: ClassTag[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> Manifest[typing.List[_ManifestFactory__SingletonTypeManifest__T]]: ...
        def canEqual(self, that: typing.Any) -> bool: ...
        def equals(self, that: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ManifestFactory__SingletonTypeManifest__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ManifestFactory__SingletonTypeManifest__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[Manifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ManifestFactory__SingletonTypeManifest__T]: ...
        def wrap(self) -> ClassTag[typing.List[_ManifestFactory__SingletonTypeManifest__T]]: ...
    class UnitManifest(AnyValManifest[scala.runtime.BoxedUnit]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self): ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def newArray(self, len: int) -> typing.List[scala.runtime.BoxedUnit]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[scala.runtime.BoxedUnit]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[scala.runtime.BoxedUnit]: ...
        def runtimeClass(self) -> typing.Type[None]: ...
        def unapply(self, x: typing.Any) -> scala.Option[scala.runtime.BoxedUnit]: ...
    class WildcardManifest(Manifest[_ManifestFactory__WildcardManifest__T], typing.Generic[_ManifestFactory__WildcardManifest__T]):
        serialVersionUID: typing.ClassVar[int] = ...
        def __init__(self, lowerBound: Manifest[typing.Any], upperBound: Manifest[typing.Any]): ...
        def $greater$colon$greater(self, that: ClassTag[typing.Any]) -> bool: ...
        def $less$colon$less(self, that: ClassTag[typing.Any]) -> bool: ...
        def argString(self) -> str: ...
        _arrayClass__T = typing.TypeVar('_arrayClass__T')  # <T>
        def arrayClass(self, tp: typing.Type[typing.Any]) -> typing.Type[typing.Any]: ...
        def arrayManifest(self) -> Manifest[typing.Any]: ...
        def canEqual(self, that: typing.Any) -> bool: ...
        def equals(self, that: typing.Any) -> bool: ...
        def erasure(self) -> typing.Type[typing.Any]: ...
        def hashCode(self) -> int: ...
        def newArray(self, len: int) -> typing.Any: ...
        def newArray2(self, len: int) -> typing.List[typing.Any]: ...
        def newArray3(self, len: int) -> typing.List[typing.List[typing.Any]]: ...
        def newArray4(self, len: int) -> typing.List[typing.List[typing.List[typing.Any]]]: ...
        def newArray5(self, len: int) -> typing.List[typing.List[typing.List[typing.List[typing.Any]]]]: ...
        def newArrayBuilder(self) -> scala.collection.mutable.ArrayBuilder[_ManifestFactory__WildcardManifest__T]: ...
        def newWrappedArray(self, len: int) -> scala.collection.mutable.WrappedArray[_ManifestFactory__WildcardManifest__T]: ...
        def runtimeClass(self) -> typing.Type[typing.Any]: ...
        def toString(self) -> str: ...
        def typeArguments(self) -> scala.collection.immutable.List[Manifest[typing.Any]]: ...
        def unapply(self, x: typing.Any) -> scala.Option[_ManifestFactory__WildcardManifest__T]: ...
        def wrap(self) -> ClassTag[typing.Any]: ...
    class : ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("scala.reflect")``.

    AnyValManifest: typing.Type[AnyValManifest]
    ClassManifestDeprecatedApis: typing.Type[ClassManifestDeprecatedApis]
    ClassManifestFactory: typing.Type[ClassManifestFactory]
    ClassTag: typing.Type[ClassTag]
    ClassTypeManifest: typing.Type[ClassTypeManifest]
    Manifest: typing.Type[Manifest]
    ManifestFactory: typing.Type[ManifestFactory]
    NameTransformer: typing.Type[NameTransformer]
    NoManifest: typing.Type[NoManifest]
    OptManifest: typing.Type[OptManifest]
    ScalaLongSignature: typing.Type[ScalaLongSignature]
    ScalaSignature: typing.Type[ScalaSignature]
    package: typing.Type[package]
    api: scala.reflect.api.__module_protocol__
    io: scala.reflect.io.__module_protocol__
    macros: scala.reflect.macros.__module_protocol__
    runtime: scala.reflect.runtime.__module_protocol__
