import org.ergoplatform.settings
import typing



class EmissionRules:
    def __init__(self, settings: org.ergoplatform.settings.MonetarySettings): ...
    @staticmethod
    def CoinsInOneErgo() -> int: ...
    def blocksTotal(self) -> int: ...
    def coinsTotal(self) -> int: ...
    def emissionAtHeight(self, h: int) -> int: ...
    def foundationRewardAtHeight(self, h: int) -> int: ...
    def foundersCoinsTotal(self) -> int: ...
    def issuedCoinsAfterHeight(self, h: int) -> int: ...
    def minersCoinsTotal(self) -> int: ...
    def minersRewardAtHeight(self, h: int) -> int: ...
    def remainingCoinsAfterHeight(self, h: int) -> int: ...
    def remainingFoundationRewardAtHeight(self, h: int) -> int: ...
    def settings(self) -> org.ergoplatform.settings.MonetarySettings: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("org.ergoplatform.mining.emission")``.

    EmissionRules: typing.Type[EmissionRules]
