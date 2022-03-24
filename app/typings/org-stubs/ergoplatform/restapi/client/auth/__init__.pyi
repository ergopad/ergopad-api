import okhttp3
import typing



class ApiKeyAuth(okhttp3.Interceptor):
    def __init__(self, string: str, string2: str): ...
    def getApiKey(self) -> str: ...
    def getLocation(self) -> str: ...
    def getParamName(self) -> str: ...
    def intercept(self, chain: okhttp3.Interceptor.Chain) -> okhttp3.Response: ...
    def setApiKey(self, string: str) -> None: ...

class HttpBasicAuth(okhttp3.Interceptor):
    def __init__(self): ...
    def getPassword(self) -> str: ...
    def getUsername(self) -> str: ...
    def intercept(self, chain: okhttp3.Interceptor.Chain) -> okhttp3.Response: ...
    def setCredentials(self, string: str, string2: str) -> None: ...
    def setPassword(self, string: str) -> None: ...
    def setUsername(self, string: str) -> None: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("org.ergoplatform.restapi.client.auth")``.

    ApiKeyAuth: typing.Type[ApiKeyAuth]
    HttpBasicAuth: typing.Type[HttpBasicAuth]
