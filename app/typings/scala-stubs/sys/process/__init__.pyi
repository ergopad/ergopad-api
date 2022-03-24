import java.io
import java.lang
import java.net
import java.util.concurrent
import jpype.protocol
import scala
import scala.collection
import scala.collection.immutable
import scala.concurrent
import scala.runtime
import typing



_BasicIO__Streamed__T = typing.TypeVar('_BasicIO__Streamed__T')  # <T>
class BasicIO:
    @staticmethod
    def BufferSize() -> int: ...
    @staticmethod
    def Newline() -> str: ...
    @typing.overload
    @staticmethod
    def apply(withIn: bool, buffer: java.lang.StringBuffer, log: scala.Option['ProcessLogger']) -> 'ProcessIO': ...
    @typing.overload
    @staticmethod
    def apply(withIn: bool, output: scala.Function1[str, scala.runtime.BoxedUnit], log: scala.Option['ProcessLogger']) -> 'ProcessIO': ...
    @typing.overload
    @staticmethod
    def apply(withIn: bool, log: 'ProcessLogger') -> 'ProcessIO': ...
    @staticmethod
    def close(c: java.io.Closeable) -> None: ...
    @staticmethod
    def connectToIn(o: java.io.OutputStream) -> None: ...
    @staticmethod
    def getErr(log: scala.Option['ProcessLogger']) -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    @staticmethod
    def input(connect: bool) -> scala.Function1[java.io.OutputStream, scala.runtime.BoxedUnit]: ...
    @typing.overload
    @staticmethod
    def processFully(buffer: java.lang.Appendable) -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    @typing.overload
    @staticmethod
    def processFully(processLine: scala.Function1[str, scala.runtime.BoxedUnit]) -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    @staticmethod
    def processLinesFully(processLine: scala.Function1[str, scala.runtime.BoxedUnit], readLine: scala.Function0[str]) -> None: ...
    @typing.overload
    @staticmethod
    def standard(connectInput: bool) -> 'ProcessIO': ...
    @typing.overload
    @staticmethod
    def standard(in_: scala.Function1[java.io.OutputStream, scala.runtime.BoxedUnit]) -> 'ProcessIO': ...
    @staticmethod
    def toStdErr() -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    @staticmethod
    def toStdOut() -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    @staticmethod
    def transferFully(in_: java.io.InputStream, out: java.io.OutputStream) -> None: ...
    class Streamed(typing.Generic[_BasicIO__Streamed__T]):
        def __init__(self, process: scala.Function1[_BasicIO__Streamed__T, scala.runtime.BoxedUnit], done: scala.Function1[typing.Any, scala.runtime.BoxedUnit], stream: scala.Function0[scala.collection.immutable.Stream[_BasicIO__Streamed__T]]): ...
        def done(self) -> scala.Function1[typing.Any, scala.runtime.BoxedUnit]: ...
        def process(self) -> scala.Function1[_BasicIO__Streamed__T, scala.runtime.BoxedUnit]: ...
        def stream(self) -> scala.Function0[scala.collection.immutable.Stream[_BasicIO__Streamed__T]]: ...
    class Streamed$:
        MODULE$: typing.ClassVar['BasicIO.Streamed.'] = ...
        def __init__(self): ...
        _apply__T = typing.TypeVar('_apply__T')  # <T>
        def apply(self, nonzeroException: bool) -> 'BasicIO.Streamed'[_apply__T]: ...
    class Uncloseable(java.io.Closeable):
        @staticmethod
        def $init$($this: 'BasicIO.Uncloseable') -> None: ...
        def close(self) -> None: ...
    class Uncloseable$:
        MODULE$: typing.ClassVar['BasicIO.Uncloseable.'] = ...
        def __init__(self): ...
        @typing.overload
        def apply(self, in_: java.io.InputStream) -> java.io.InputStream: ...
        @typing.overload
        def apply(self, out: java.io.OutputStream) -> java.io.OutputStream: ...
        @typing.overload
        def protect(self, in_: java.io.InputStream) -> java.io.InputStream: ...
        @typing.overload
        def protect(self, out: java.io.OutputStream) -> java.io.OutputStream: ...

class Process:
    @typing.overload
    @staticmethod
    def apply(value: bool) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(builder: java.lang.ProcessBuilder) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: str) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: str, cwd: typing.Union[java.io.File, jpype.protocol.SupportsPath], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(name: str, exitValue: scala.Function0[typing.Any]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: str, cwd: scala.Option[typing.Union[java.io.File, jpype.protocol.SupportsPath]], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: str, arguments: scala.collection.Seq[str]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: scala.collection.Seq[str]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: scala.collection.Seq[str], cwd: typing.Union[java.io.File, jpype.protocol.SupportsPath], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(command: scala.collection.Seq[str], cwd: scala.Option[typing.Union[java.io.File, jpype.protocol.SupportsPath]], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def apply(file: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder.FileBuilder': ...
    @typing.overload
    @staticmethod
    def apply(url: java.net.URL) -> 'ProcessBuilder.URLBuilder': ...
    _applySeq__T = typing.TypeVar('_applySeq__T')  # <T>
    @staticmethod
    def applySeq(builders: scala.collection.Seq[_applySeq__T], convert: scala.Function1[_applySeq__T, 'ProcessBuilder.Source']) -> scala.collection.Seq['ProcessBuilder.Source']: ...
    @typing.overload
    @staticmethod
    def cat(files: scala.collection.Seq['ProcessBuilder.Source']) -> 'ProcessBuilder': ...
    @typing.overload
    @staticmethod
    def cat(file: 'ProcessBuilder.Source', files: scala.collection.Seq['ProcessBuilder.Source']) -> 'ProcessBuilder': ...
    def destroy(self) -> None: ...
    def exitValue(self) -> int: ...
    def isAlive(self) -> bool: ...

class ProcessCreation:
    @staticmethod
    def $init$($this: 'ProcessCreation') -> None: ...
    @typing.overload
    def apply(self, value: bool) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, builder: java.lang.ProcessBuilder) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: str) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: str, cwd: typing.Union[java.io.File, jpype.protocol.SupportsPath], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, name: str, exitValue: scala.Function0[typing.Any]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: str, cwd: scala.Option[typing.Union[java.io.File, jpype.protocol.SupportsPath]], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: str, arguments: scala.collection.Seq[str]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: scala.collection.Seq[str]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: scala.collection.Seq[str], cwd: typing.Union[java.io.File, jpype.protocol.SupportsPath], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, command: scala.collection.Seq[str], cwd: scala.Option[typing.Union[java.io.File, jpype.protocol.SupportsPath]], extraEnv: scala.collection.Seq[scala.Tuple2[str, str]]) -> 'ProcessBuilder': ...
    @typing.overload
    def apply(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder.FileBuilder': ...
    @typing.overload
    def apply(self, url: java.net.URL) -> 'ProcessBuilder.URLBuilder': ...
    _applySeq__T = typing.TypeVar('_applySeq__T')  # <T>
    def applySeq(self, builders: scala.collection.Seq[_applySeq__T], convert: scala.Function1[_applySeq__T, 'ProcessBuilder.Source']) -> scala.collection.Seq['ProcessBuilder.Source']: ...
    @typing.overload
    def cat(self, files: scala.collection.Seq['ProcessBuilder.Source']) -> 'ProcessBuilder': ...
    @typing.overload
    def cat(self, file: 'ProcessBuilder.Source', files: scala.collection.Seq['ProcessBuilder.Source']) -> 'ProcessBuilder': ...

class ProcessIO:
    @typing.overload
    def __init__(self, in_: scala.Function1[java.io.OutputStream, scala.runtime.BoxedUnit], out: scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit], err: scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]): ...
    @typing.overload
    def __init__(self, writeInput: scala.Function1[java.io.OutputStream, scala.runtime.BoxedUnit], processOutput: scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit], processError: scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit], daemonizeThreads: bool): ...
    def daemonizeThreads(self) -> bool: ...
    def daemonized(self) -> 'ProcessIO': ...
    def processError(self) -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    def processOutput(self) -> scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]: ...
    def withError(self, process: scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]) -> 'ProcessIO': ...
    def withInput(self, write: scala.Function1[java.io.OutputStream, scala.runtime.BoxedUnit]) -> 'ProcessIO': ...
    def withOutput(self, process: scala.Function1[java.io.InputStream, scala.runtime.BoxedUnit]) -> 'ProcessIO': ...
    def writeInput(self) -> scala.Function1[java.io.OutputStream, scala.runtime.BoxedUnit]: ...

class ProcessImplicits:
    @staticmethod
    def $init$($this: 'ProcessImplicits') -> None: ...
    def builderToProcess(self, builder: java.lang.ProcessBuilder) -> 'ProcessBuilder': ...
    _buildersToProcess__T = typing.TypeVar('_buildersToProcess__T')  # <T>
    def buildersToProcess(self, builders: scala.collection.Seq[_buildersToProcess__T], convert: scala.Function1[_buildersToProcess__T, 'ProcessBuilder.Source']) -> scala.collection.Seq['ProcessBuilder.Source']: ...
    def fileToProcess(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder.FileBuilder': ...
    def stringSeqToProcess(self, command: scala.collection.Seq[str]) -> 'ProcessBuilder': ...
    def stringToProcess(self, command: str) -> 'ProcessBuilder': ...
    def urlToProcess(self, url: java.net.URL) -> 'ProcessBuilder.URLBuilder': ...

class ProcessLogger:
    @typing.overload
    @staticmethod
    def apply(file: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'FileProcessLogger': ...
    @typing.overload
    @staticmethod
    def apply(fn: scala.Function1[str, scala.runtime.BoxedUnit]) -> 'ProcessLogger': ...
    @typing.overload
    @staticmethod
    def apply(fout: scala.Function1[str, scala.runtime.BoxedUnit], ferr: scala.Function1[str, scala.runtime.BoxedUnit]) -> 'ProcessLogger': ...
    _buffer__T = typing.TypeVar('_buffer__T')  # <T>
    def buffer(self, f: scala.Function0[_buffer__T]) -> _buffer__T: ...
    def err(self, s: scala.Function0[str]) -> None: ...
    def out(self, s: scala.Function0[str]) -> None: ...

class package:
    @staticmethod
    def builderToProcess(builder: java.lang.ProcessBuilder) -> 'ProcessBuilder': ...
    _buildersToProcess__T = typing.TypeVar('_buildersToProcess__T')  # <T>
    @staticmethod
    def buildersToProcess(builders: scala.collection.Seq[_buildersToProcess__T], convert: scala.Function1[_buildersToProcess__T, 'ProcessBuilder.Source']) -> scala.collection.Seq['ProcessBuilder.Source']: ...
    @staticmethod
    def fileToProcess(file: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder.FileBuilder': ...
    @staticmethod
    def javaVmArguments() -> scala.collection.immutable.List[str]: ...
    @staticmethod
    def stderr() -> java.io.PrintStream: ...
    @staticmethod
    def stdin() -> java.io.InputStream: ...
    @staticmethod
    def stdout() -> java.io.PrintStream: ...
    @staticmethod
    def stringSeqToProcess(command: scala.collection.Seq[str]) -> 'ProcessBuilder': ...
    @staticmethod
    def stringToProcess(command: str) -> 'ProcessBuilder': ...
    @staticmethod
    def urlToProcess(url: java.net.URL) -> 'ProcessBuilder.URLBuilder': ...

class processInternal:
    @staticmethod
    def dbg(msgs: scala.collection.Seq[typing.Any]) -> None: ...
    _ioFailure__T = typing.TypeVar('_ioFailure__T')  # <T>
    @staticmethod
    def ioFailure(handler: scala.Function1[java.io.IOException, _ioFailure__T]) -> scala.PartialFunction[java.lang.Throwable, _ioFailure__T]: ...
    _onError__T = typing.TypeVar('_onError__T')  # <T>
    @staticmethod
    def onError(handler: scala.Function1[java.lang.Throwable, _onError__T]) -> scala.PartialFunction[java.lang.Throwable, _onError__T]: ...
    _onIOInterrupt__T = typing.TypeVar('_onIOInterrupt__T')  # <T>
    @staticmethod
    def onIOInterrupt(handler: scala.Function0[_onIOInterrupt__T]) -> scala.PartialFunction[java.lang.Throwable, _onIOInterrupt__T]: ...
    _onInterrupt__T = typing.TypeVar('_onInterrupt__T')  # <T>
    @staticmethod
    def onInterrupt(handler: scala.Function0[_onInterrupt__T]) -> scala.PartialFunction[java.lang.Throwable, _onInterrupt__T]: ...
    @staticmethod
    def processDebug() -> bool: ...

class FileProcessLogger(ProcessLogger, java.io.Closeable, java.io.Flushable):
    def __init__(self, file: typing.Union[java.io.File, jpype.protocol.SupportsPath]): ...
    _buffer__T = typing.TypeVar('_buffer__T')  # <T>
    def buffer(self, f: scala.Function0[_buffer__T]) -> _buffer__T: ...
    def close(self) -> None: ...
    def err(self, s: scala.Function0[str]) -> None: ...
    def flush(self) -> None: ...
    def out(self, s: scala.Function0[str]) -> None: ...

class ProcessBuilder(scala.sys.process.ProcessBuilder.Source, scala.sys.process.ProcessBuilder.Sink):
    @typing.overload
    def $bang(self) -> int: ...
    @typing.overload
    def $bang(self, log: ProcessLogger) -> int: ...
    @typing.overload
    def $bang$bang(self) -> str: ...
    @typing.overload
    def $bang$bang(self, log: ProcessLogger) -> str: ...
    @typing.overload
    def $bang$bang$less(self) -> str: ...
    @typing.overload
    def $bang$bang$less(self, log: ProcessLogger) -> str: ...
    @typing.overload
    def $bang$less(self) -> int: ...
    @typing.overload
    def $bang$less(self, log: ProcessLogger) -> int: ...
    def $hash$amp$amp(self, other: 'ProcessBuilder') -> 'ProcessBuilder': ...
    def $hash$bar(self, other: 'ProcessBuilder') -> 'ProcessBuilder': ...
    def $hash$bar$bar(self, other: 'ProcessBuilder') -> 'ProcessBuilder': ...
    def $hash$hash$hash(self, other: 'ProcessBuilder') -> 'ProcessBuilder': ...
    @staticmethod
    def $init$($this: 'ProcessBuilder') -> None: ...
    def canPipeTo(self) -> bool: ...
    def hasExitValue(self) -> bool: ...
    @typing.overload
    def lineStream(self) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lineStream(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lineStream_$bang(self) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lineStream_$bang(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lines(self) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lines(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lines_$bang(self) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def lines_$bang(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
    @typing.overload
    def run(self) -> Process: ...
    @typing.overload
    def run(self, connectInput: bool) -> Process: ...
    @typing.overload
    def run(self, io: ProcessIO) -> Process: ...
    @typing.overload
    def run(self, log: ProcessLogger) -> Process: ...
    @typing.overload
    def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
    class FileBuilder(scala.sys.process.ProcessBuilder.Sink, scala.sys.process.ProcessBuilder.Source):
        @typing.overload
        def $hash$less$less(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$less$less(self, u: java.net.URL) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$less$less(self, i: scala.Function0[java.io.InputStream]) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$less$less(self, p: 'ProcessBuilder') -> 'ProcessBuilder': ...
    class Sink:
        @typing.overload
        def $hash$less(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$less(self, f: java.net.URL) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$less(self, in_: scala.Function0[java.io.InputStream]) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$less(self, b: 'ProcessBuilder') -> 'ProcessBuilder': ...
        @staticmethod
        def $init$($this: 'ProcessBuilder.Sink') -> None: ...
        def toSink(self) -> 'ProcessBuilder': ...
    class Source:
        @typing.overload
        def $hash$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$greater(self, out: scala.Function0[java.io.OutputStream]) -> 'ProcessBuilder': ...
        @typing.overload
        def $hash$greater(self, b: 'ProcessBuilder') -> 'ProcessBuilder': ...
        def $hash$greater$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> 'ProcessBuilder': ...
        @staticmethod
        def $init$($this: 'ProcessBuilder.Source') -> None: ...
        def cat(self) -> 'ProcessBuilder': ...
        def toSource(self) -> 'ProcessBuilder': ...
    class URLBuilder(scala.sys.process.ProcessBuilder.Source): ...

class ProcessBuilderImpl:
    @staticmethod
    def $init$($this: 'ProcessBuilderImpl') -> None: ...
    class AbstractBuilder(ProcessBuilder):
        $outer: 'ProcessBuilder.' = ...
        def __init__(self, $outer: 'ProcessBuilder.'): ...
        @typing.overload
        def $bang(self) -> int: ...
        @typing.overload
        def $bang(self, io: ProcessIO) -> int: ...
        @typing.overload
        def $bang(self, log: ProcessLogger) -> int: ...
        @typing.overload
        def $bang$bang(self) -> str: ...
        @typing.overload
        def $bang$bang(self, log: ProcessLogger) -> str: ...
        @typing.overload
        def $bang$bang$less(self) -> str: ...
        @typing.overload
        def $bang$bang$less(self, log: ProcessLogger) -> str: ...
        @typing.overload
        def $bang$less(self) -> int: ...
        @typing.overload
        def $bang$less(self, log: ProcessLogger) -> int: ...
        def $hash$amp$amp(self, other: ProcessBuilder) -> ProcessBuilder: ...
        def $hash$bar(self, other: ProcessBuilder) -> ProcessBuilder: ...
        def $hash$bar$bar(self, other: ProcessBuilder) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, out: scala.Function0[java.io.OutputStream]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, b: ProcessBuilder) -> ProcessBuilder: ...
        def $hash$greater$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        def $hash$hash$hash(self, other: ProcessBuilder) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, f: java.net.URL) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, in_: scala.Function0[java.io.InputStream]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, b: ProcessBuilder) -> ProcessBuilder: ...
        def canPipeTo(self) -> bool: ...
        def cat(self) -> ProcessBuilder: ...
        def daemonized(self) -> ProcessBuilder: ...
        def hasExitValue(self) -> bool: ...
        @typing.overload
        def lineStream(self) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lineStream(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lineStream_$bang(self) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lineStream_$bang(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lines(self) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lines(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lines_$bang(self) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def lines_$bang(self, log: ProcessLogger) -> scala.collection.immutable.Stream[str]: ...
        @typing.overload
        def run(self, io: ProcessIO) -> Process: ...
        @typing.overload
        def run(self) -> Process: ...
        @typing.overload
        def run(self, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
        def toSink(self) -> 'ProcessBuilderImpl.AbstractBuilder': ...
        def toSource(self) -> 'ProcessBuilderImpl.AbstractBuilder': ...
    class AndBuilder(scala.sys.process.ProcessBuilderImpl.SequentialBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', first: ProcessBuilder, second: ProcessBuilder): ...
        def createProcess(self, io: ProcessIO) -> 'ProcessImpl.AndProcess': ...
    class BasicBuilder(scala.sys.process.ProcessBuilderImpl.AbstractBuilder):
        def __init__(self, $outer: 'ProcessBuilder.'): ...
        def checkNotThis(self, a: ProcessBuilder) -> None: ...
        def createProcess(self, io: ProcessIO) -> 'ProcessImpl.BasicProcess': ...
        @typing.overload
        def run(self, io: ProcessIO) -> Process: ...
        @typing.overload
        def run(self) -> Process: ...
        @typing.overload
        def run(self, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
    class DaemonBuilder(scala.sys.process.ProcessBuilderImpl.AbstractBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', underlying: ProcessBuilder): ...
        @typing.overload
        def run(self, io: ProcessIO) -> Process: ...
        @typing.overload
        def run(self) -> Process: ...
        @typing.overload
        def run(self, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
    class Dummy(scala.sys.process.ProcessBuilderImpl.AbstractBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', toString: str, exitValue: scala.Function0[typing.Any]): ...
        def canPipeTo(self) -> bool: ...
        @typing.overload
        def run(self) -> Process: ...
        @typing.overload
        def run(self, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, io: ProcessIO) -> Process: ...
        def toString(self) -> str: ...
    class FileImpl(ProcessBuilder.FileBuilder):
        $outer: 'ProcessBuilder.' = ...
        def __init__(self, $outer: 'ProcessBuilder.', base: typing.Union[java.io.File, jpype.protocol.SupportsPath]): ...
        @typing.overload
        def $hash$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, out: scala.Function0[java.io.OutputStream]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, b: ProcessBuilder) -> ProcessBuilder: ...
        def $hash$greater$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, f: java.net.URL) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, in_: scala.Function0[java.io.InputStream]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less(self, b: ProcessBuilder) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less$less(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less$less(self, u: java.net.URL) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less$less(self, s: scala.Function0[java.io.InputStream]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$less$less(self, b: ProcessBuilder) -> ProcessBuilder: ...
        def cat(self) -> ProcessBuilder: ...
        def toSink(self) -> 'ProcessBuilderImpl.FileOutput': ...
        def toSource(self) -> 'ProcessBuilderImpl.FileInput': ...
    class FileInput(scala.sys.process.ProcessBuilderImpl.IStreamBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', file: typing.Union[java.io.File, jpype.protocol.SupportsPath]): ...
    class FileOutput(scala.sys.process.ProcessBuilderImpl.OStreamBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', file: typing.Union[java.io.File, jpype.protocol.SupportsPath], append: bool): ...
    class IStreamBuilder(scala.sys.process.ProcessBuilderImpl.ThreadBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', stream: scala.Function0[java.io.InputStream], label: str): ...
        def hasExitValue(self) -> bool: ...
    class OStreamBuilder(scala.sys.process.ProcessBuilderImpl.ThreadBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', stream: scala.Function0[java.io.OutputStream], label: str): ...
        def hasExitValue(self) -> bool: ...
    class OrBuilder(scala.sys.process.ProcessBuilderImpl.SequentialBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', first: ProcessBuilder, second: ProcessBuilder): ...
        def createProcess(self, io: ProcessIO) -> 'ProcessImpl.OrProcess': ...
    class PipedBuilder(scala.sys.process.ProcessBuilderImpl.SequentialBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', first: ProcessBuilder, second: ProcessBuilder, toError: bool): ...
        def createProcess(self, io: ProcessIO) -> 'ProcessImpl.PipedProcesses': ...
    class SequenceBuilder(scala.sys.process.ProcessBuilderImpl.SequentialBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', first: ProcessBuilder, second: ProcessBuilder): ...
        def createProcess(self, io: ProcessIO) -> 'ProcessImpl.ProcessSequence': ...
    class SequentialBuilder(scala.sys.process.ProcessBuilderImpl.BasicBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', a: ProcessBuilder, b: ProcessBuilder, operatorString: str): ...
        def toString(self) -> str: ...
    class Simple(scala.sys.process.ProcessBuilderImpl.AbstractBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', p: java.lang.ProcessBuilder): ...
        def canPipeTo(self) -> bool: ...
        @typing.overload
        def run(self) -> Process: ...
        @typing.overload
        def run(self, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, io: ProcessIO) -> Process: ...
        def toString(self) -> str: ...
    class ThreadBuilder(scala.sys.process.ProcessBuilderImpl.AbstractBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', toString: str, runImpl: scala.Function1[ProcessIO, scala.runtime.BoxedUnit]): ...
        @typing.overload
        def run(self) -> Process: ...
        @typing.overload
        def run(self, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger) -> Process: ...
        @typing.overload
        def run(self, log: ProcessLogger, connectInput: bool) -> Process: ...
        @typing.overload
        def run(self, io: ProcessIO) -> Process: ...
        def toString(self) -> str: ...
    class URLImpl(ProcessBuilder.URLBuilder):
        $outer: 'ProcessBuilder.' = ...
        def __init__(self, $outer: 'ProcessBuilder.', url: java.net.URL): ...
        @typing.overload
        def $hash$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, out: scala.Function0[java.io.OutputStream]) -> ProcessBuilder: ...
        @typing.overload
        def $hash$greater(self, b: ProcessBuilder) -> ProcessBuilder: ...
        def $hash$greater$greater(self, f: typing.Union[java.io.File, jpype.protocol.SupportsPath]) -> ProcessBuilder: ...
        def cat(self) -> ProcessBuilder: ...
        def toSource(self) -> 'ProcessBuilderImpl.URLInput': ...
    class URLInput(scala.sys.process.ProcessBuilderImpl.IStreamBuilder):
        def __init__(self, $outer: 'ProcessBuilder.', url: java.net.URL): ...

class ProcessImpl:
    @staticmethod
    def $init$($this: 'ProcessImpl') -> None: ...
    def Future(self) -> 'ProcessImpl.Future.': ...
    def Spawn(self) -> 'ProcessImpl.Spawn.': ...
    class AndProcess(scala.sys.process.ProcessImpl.SequentialProcess):
        def __init__(self, $outer: 'Process.', a: ProcessBuilder, b: ProcessBuilder, io: ProcessIO): ...
    class BasicProcess(Process):
        $outer: 'Process.' = ...
        def __init__(self, $outer: 'Process.'): ...
        def start(self) -> None: ...
    class CompoundProcess(scala.sys.process.ProcessImpl.BasicProcess):
        def __init__(self, $outer: 'Process.'): ...
        def destroy(self) -> None: ...
        def destroyer(self) -> scala.Function0[scala.runtime.BoxedUnit]: ...
        def exitValue(self) -> int: ...
        def futureThread(self) -> java.lang.Thread: ...
        def futureValue(self) -> scala.Function0[scala.Option[typing.Any]]: ...
        def isAlive(self) -> bool: ...
        def processThread(self) -> java.lang.Thread: ...
        def runAndExitValue(self) -> scala.Option[typing.Any]: ...
        _runInterruptible__T = typing.TypeVar('_runInterruptible__T')  # <T>
        def runInterruptible(self, action: scala.Function0[_runInterruptible__T], destroyImpl: scala.Function0[scala.runtime.BoxedUnit]) -> scala.Option[_runInterruptible__T]: ...
        def start(self) -> None: ...
    class DummyProcess(Process):
        $outer: 'Process.' = ...
        def __init__(self, $outer: 'Process.', action: scala.Function0[typing.Any]): ...
        def destroy(self) -> None: ...
        def exitValue(self) -> int: ...
        def isAlive(self) -> bool: ...
    class Future$:
        def __init__(self, $outer: 'Process.'): ...
        _apply__T = typing.TypeVar('_apply__T')  # <T>
        def apply(self, f: scala.Function0[_apply__T]) -> scala.Tuple2[java.lang.Thread, scala.Function0[_apply__T]]: ...
    class OrProcess(scala.sys.process.ProcessImpl.SequentialProcess):
        def __init__(self, $outer: 'Process.', a: ProcessBuilder, b: ProcessBuilder, io: ProcessIO): ...
    class PipeSink(scala.sys.process.ProcessImpl.PipeThread):
        def __init__(self, $outer: 'Process.', label: scala.Function0[str]): ...
        def connectIn(self, pipeOut: java.io.PipedOutputStream) -> None: ...
        def connectOut(self, out: java.io.OutputStream) -> None: ...
        def pipe(self) -> java.io.PipedInputStream: ...
        def release(self) -> None: ...
        def run(self) -> None: ...
        def sink(self) -> java.util.concurrent.LinkedBlockingQueue[scala.Option[java.io.OutputStream]]: ...
    class PipeSource(scala.sys.process.ProcessImpl.PipeThread):
        def __init__(self, $outer: 'Process.', label: scala.Function0[str]): ...
        def connectIn(self, in_: java.io.InputStream) -> None: ...
        def connectOut(self, sink: 'ProcessImpl.PipeSink') -> None: ...
        def pipe(self) -> java.io.PipedOutputStream: ...
        def release(self) -> None: ...
        def run(self) -> None: ...
        def source(self) -> java.util.concurrent.LinkedBlockingQueue[scala.Option[java.io.InputStream]]: ...
    class PipeThread(java.lang.Thread):
        $outer: 'Process.' = ...
        def __init__(self, $outer: 'Process.', isSink: bool, labelFn: scala.Function0[str]): ...
        def run(self) -> None: ...
        def runloop(self, src: java.io.InputStream, dst: java.io.OutputStream) -> None: ...
    class PipedProcesses(scala.sys.process.ProcessImpl.CompoundProcess):
        def __init__(self, $outer: 'Process.', a: ProcessBuilder, b: ProcessBuilder, defaultIO: ProcessIO, toError: bool): ...
        @typing.overload
        def runAndExitValue(self) -> scala.Option[typing.Any]: ...
        @typing.overload
        def runAndExitValue(self, source: 'ProcessImpl.PipeSource', sink: 'ProcessImpl.PipeSink') -> scala.Option[typing.Any]: ...
    class ProcessSequence(scala.sys.process.ProcessImpl.SequentialProcess):
        def __init__(self, $outer: 'Process.', a: ProcessBuilder, b: ProcessBuilder, io: ProcessIO): ...
    class SequentialProcess(scala.sys.process.ProcessImpl.CompoundProcess):
        def __init__(self, $outer: 'Process.', a: ProcessBuilder, b: ProcessBuilder, io: ProcessIO, evaluateSecondProcess: scala.Function1[typing.Any, typing.Any]): ...
        def runAndExitValue(self) -> scala.Option[typing.Any]: ...
    class SimpleProcess(Process):
        $outer: 'Process.' = ...
        def __init__(self, $outer: 'Process.', p: java.lang.Process, inputThread: java.lang.Thread, outputThreads: scala.collection.immutable.List[java.lang.Thread]): ...
        def destroy(self) -> None: ...
        def exitValue(self) -> int: ...
        def isAlive(self) -> bool: ...
    class Spawn$:
        def __init__(self, $outer: 'Process.'): ...
        @typing.overload
        def apply(self, f: scala.Function0[scala.runtime.BoxedUnit]) -> java.lang.Thread: ...
        @typing.overload
        def apply(self, f: scala.Function0[scala.runtime.BoxedUnit], daemon: bool) -> java.lang.Thread: ...
    class ThreadProcess(Process):
        def __init__(self, $outer: 'Process.', thread: java.lang.Thread, success: scala.concurrent.SyncVar[typing.Any]): ...
        def destroy(self) -> None: ...
        def exitValue(self) -> int: ...
        def isAlive(self) -> bool: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("scala.sys.process")``.

    BasicIO: typing.Type[BasicIO]
    FileProcessLogger: typing.Type[FileProcessLogger]
    Process: typing.Type[Process]
    ProcessBuilder: typing.Type[ProcessBuilder]
    ProcessBuilderImpl: typing.Type[ProcessBuilderImpl]
    ProcessCreation: typing.Type[ProcessCreation]
    ProcessIO: typing.Type[ProcessIO]
    ProcessImpl: typing.Type[ProcessImpl]
    ProcessImplicits: typing.Type[ProcessImplicits]
    ProcessLogger: typing.Type[ProcessLogger]
    package: typing.Type[package]
    processInternal: typing.Type[processInternal]
