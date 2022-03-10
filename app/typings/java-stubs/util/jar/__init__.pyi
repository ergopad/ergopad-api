import java.io
import java.lang
import java.security
import java.security.cert
import java.util
import java.util.stream
import java.util.zip
import jpype.protocol
import typing



class Attributes(java.util.Map[typing.Any, typing.Any], java.lang.Cloneable):
    @typing.overload
    def __init__(self): ...
    @typing.overload
    def __init__(self, int: int): ...
    @typing.overload
    def __init__(self, attributes: 'Attributes'): ...
    def clear(self) -> None: ...
    def clone(self) -> typing.Any: ...
    def containsKey(self, object: typing.Any) -> bool: ...
    def containsValue(self, object: typing.Any) -> bool: ...
    def entrySet(self) -> java.util.Set[java.util.Map.Entry[typing.Any, typing.Any]]: ...
    def equals(self, object: typing.Any) -> bool: ...
    def get(self, object: typing.Any) -> typing.Any: ...
    @typing.overload
    def getValue(self, string: str) -> str: ...
    @typing.overload
    def getValue(self, name: 'Attributes.Name') -> str: ...
    def hashCode(self) -> int: ...
    def isEmpty(self) -> bool: ...
    def keySet(self) -> java.util.Set[typing.Any]: ...
    def put(self, object: typing.Any, object2: typing.Any) -> typing.Any: ...
    def putAll(self, map: typing.Union[java.util.Map[typing.Any, typing.Any], typing.Mapping[typing.Any, typing.Any]]) -> None: ...
    def putValue(self, string: str, string2: str) -> str: ...
    @typing.overload
    def remove(self, object: typing.Any, object2: typing.Any) -> bool: ...
    @typing.overload
    def remove(self, object: typing.Any) -> typing.Any: ...
    def size(self) -> int: ...
    def values(self) -> java.util.Collection[typing.Any]: ...
    class Name:
        MANIFEST_VERSION: typing.ClassVar['Attributes.Name'] = ...
        SIGNATURE_VERSION: typing.ClassVar['Attributes.Name'] = ...
        CONTENT_TYPE: typing.ClassVar['Attributes.Name'] = ...
        CLASS_PATH: typing.ClassVar['Attributes.Name'] = ...
        MAIN_CLASS: typing.ClassVar['Attributes.Name'] = ...
        SEALED: typing.ClassVar['Attributes.Name'] = ...
        EXTENSION_LIST: typing.ClassVar['Attributes.Name'] = ...
        EXTENSION_NAME: typing.ClassVar['Attributes.Name'] = ...
        EXTENSION_INSTALLATION: typing.ClassVar['Attributes.Name'] = ...
        IMPLEMENTATION_TITLE: typing.ClassVar['Attributes.Name'] = ...
        IMPLEMENTATION_VERSION: typing.ClassVar['Attributes.Name'] = ...
        IMPLEMENTATION_VENDOR: typing.ClassVar['Attributes.Name'] = ...
        IMPLEMENTATION_VENDOR_ID: typing.ClassVar['Attributes.Name'] = ...
        IMPLEMENTATION_URL: typing.ClassVar['Attributes.Name'] = ...
        SPECIFICATION_TITLE: typing.ClassVar['Attributes.Name'] = ...
        SPECIFICATION_VERSION: typing.ClassVar['Attributes.Name'] = ...
        SPECIFICATION_VENDOR: typing.ClassVar['Attributes.Name'] = ...
        MULTI_RELEASE: typing.ClassVar['Attributes.Name'] = ...
        def __init__(self, string: str): ...
        def equals(self, object: typing.Any) -> bool: ...
        def hashCode(self) -> int: ...
        def toString(self) -> str: ...

class JarEntry(java.util.zip.ZipEntry):
    @typing.overload
    def __init__(self, string: str): ...
    @typing.overload
    def __init__(self, jarEntry: 'JarEntry'): ...
    @typing.overload
    def __init__(self, zipEntry: java.util.zip.ZipEntry): ...
    def getAttributes(self) -> Attributes: ...
    def getCertificates(self) -> typing.List[java.security.cert.Certificate]: ...
    def getCodeSigners(self) -> typing.List[java.security.CodeSigner]: ...
    def getRealName(self) -> str: ...

class JarException(java.util.zip.ZipException):
    @typing.overload
    def __init__(self): ...
    @typing.overload
    def __init__(self, string: str): ...

class JarFile(java.util.zip.ZipFile):
    MANIFEST_NAME: typing.ClassVar[str] = ...
    @typing.overload
    def __init__(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath]): ...
    @typing.overload
    def __init__(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath], boolean: bool): ...
    @typing.overload
    def __init__(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath], boolean: bool, int: int): ...
    @typing.overload
    def __init__(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath], boolean: bool, int: int, version: java.lang.Runtime.Version): ...
    @typing.overload
    def __init__(self, string: str): ...
    @typing.overload
    def __init__(self, string: str, boolean: bool): ...
    @staticmethod
    def baseVersion() -> java.lang.Runtime.Version: ...
    def entries(self) -> java.util.Enumeration[JarEntry]: ...
    def getEntry(self, string: str) -> java.util.zip.ZipEntry: ...
    def getInputStream(self, zipEntry: java.util.zip.ZipEntry) -> java.io.InputStream: ...
    def getJarEntry(self, string: str) -> JarEntry: ...
    def getManifest(self) -> 'Manifest': ...
    def getVersion(self) -> java.lang.Runtime.Version: ...
    def isMultiRelease(self) -> bool: ...
    @staticmethod
    def runtimeVersion() -> java.lang.Runtime.Version: ...
    def stream(self) -> java.util.stream.Stream[JarEntry]: ...
    def versionedStream(self) -> java.util.stream.Stream[JarEntry]: ...

class JarInputStream(java.util.zip.ZipInputStream):
    @typing.overload
    def __init__(self, inputStream: java.io.InputStream): ...
    @typing.overload
    def __init__(self, inputStream: java.io.InputStream, boolean: bool): ...
    def getManifest(self) -> 'Manifest': ...
    def getNextEntry(self) -> java.util.zip.ZipEntry: ...
    def getNextJarEntry(self) -> JarEntry: ...
    @typing.overload
    def read(self, byteArray: typing.List[int]) -> int: ...
    @typing.overload
    def read(self, byteArray: typing.List[int], int: int, int2: int) -> int: ...
    @typing.overload
    def read(self) -> int: ...

class JarOutputStream(java.util.zip.ZipOutputStream):
    @typing.overload
    def __init__(self, outputStream: java.io.OutputStream): ...
    @typing.overload
    def __init__(self, outputStream: java.io.OutputStream, manifest: 'Manifest'): ...
    def putNextEntry(self, zipEntry: java.util.zip.ZipEntry) -> None: ...

class Manifest(java.lang.Cloneable):
    @typing.overload
    def __init__(self): ...
    @typing.overload
    def __init__(self, inputStream: java.io.InputStream): ...
    @typing.overload
    def __init__(self, manifest: 'Manifest'): ...
    def clear(self) -> None: ...
    def clone(self) -> typing.Any: ...
    def equals(self, object: typing.Any) -> bool: ...
    def getAttributes(self, string: str) -> Attributes: ...
    def getEntries(self) -> java.util.Map[str, Attributes]: ...
    def getMainAttributes(self) -> Attributes: ...
    def hashCode(self) -> int: ...
    def read(self, inputStream: java.io.InputStream) -> None: ...
    def write(self, outputStream: java.io.OutputStream) -> None: ...

class Pack200:
    @staticmethod
    def newPacker() -> 'Pack200.Packer': ...
    @staticmethod
    def newUnpacker() -> 'Pack200.Unpacker': ...
    class Packer:
        SEGMENT_LIMIT: typing.ClassVar[str] = ...
        KEEP_FILE_ORDER: typing.ClassVar[str] = ...
        EFFORT: typing.ClassVar[str] = ...
        DEFLATE_HINT: typing.ClassVar[str] = ...
        MODIFICATION_TIME: typing.ClassVar[str] = ...
        PASS_FILE_PFX: typing.ClassVar[str] = ...
        UNKNOWN_ATTRIBUTE: typing.ClassVar[str] = ...
        CLASS_ATTRIBUTE_PFX: typing.ClassVar[str] = ...
        FIELD_ATTRIBUTE_PFX: typing.ClassVar[str] = ...
        METHOD_ATTRIBUTE_PFX: typing.ClassVar[str] = ...
        CODE_ATTRIBUTE_PFX: typing.ClassVar[str] = ...
        PROGRESS: typing.ClassVar[str] = ...
        KEEP: typing.ClassVar[str] = ...
        PASS: typing.ClassVar[str] = ...
        STRIP: typing.ClassVar[str] = ...
        ERROR: typing.ClassVar[str] = ...
        TRUE: typing.ClassVar[str] = ...
        FALSE: typing.ClassVar[str] = ...
        LATEST: typing.ClassVar[str] = ...
        @typing.overload
        def pack(self, jarFile: JarFile, outputStream: java.io.OutputStream) -> None: ...
        @typing.overload
        def pack(self, jarInputStream: JarInputStream, outputStream: java.io.OutputStream) -> None: ...
        def properties(self) -> java.util.SortedMap[str, str]: ...
    class Unpacker:
        KEEP: typing.ClassVar[str] = ...
        TRUE: typing.ClassVar[str] = ...
        FALSE: typing.ClassVar[str] = ...
        DEFLATE_HINT: typing.ClassVar[str] = ...
        PROGRESS: typing.ClassVar[str] = ...
        def properties(self) -> java.util.SortedMap[str, str]: ...
        @typing.overload
        def unpack(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath], jarOutputStream: JarOutputStream) -> None: ...
        @typing.overload
        def unpack(self, inputStream: java.io.InputStream, jarOutputStream: JarOutputStream) -> None: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("java.util.jar")``.

    Attributes: typing.Type[Attributes]
    JarEntry: typing.Type[JarEntry]
    JarException: typing.Type[JarException]
    JarFile: typing.Type[JarFile]
    JarInputStream: typing.Type[JarInputStream]
    JarOutputStream: typing.Type[JarOutputStream]
    Manifest: typing.Type[Manifest]
    Pack200: typing.Type[Pack200]
