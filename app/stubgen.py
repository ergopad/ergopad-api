import jpype
import stubgenj

jpype.startJVM(None, convertStrings=True)  # noqa
jpype.addClassPath('jars/*')
import jpype.imports  # noqa
import java.util  # noqa
import org.ergoplatform
import scala
import special.collection

stubgenj.generateJavaStubs([java.util,org.ergoplatform,scala,special.collection], useStubsSuffix=True)