import jpype
import stubgenj

jpype.startJVM(None, convertStrings=True)  # noqa
jpype.addClassPath('./jars/*')
import jpype.imports  # noqa
import java.util  # noqa
import org.ergoplatform
import scala
import special.collection
import sigmastate.Values
import sigmastate.eval
import sigmastate.lang
import sigmastate.serialization

stubgenj.generateJavaStubs([java.util,org.ergoplatform,scala,special.collection,sigmastate.Values,sigmastate.eval,sigmastate.lang,sigmastate.serialization], useStubsSuffix=True)