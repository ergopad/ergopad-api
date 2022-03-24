import datetime
import java.io
import java.lang
import java.time
import java.util
import typing



class ZoneOffsetTransition(java.lang.Comparable['ZoneOffsetTransition'], java.io.Serializable):
    def compareTo(self, zoneOffsetTransition: 'ZoneOffsetTransition') -> int: ...
    def equals(self, object: typing.Any) -> bool: ...
    def getDateTimeAfter(self) -> java.time.LocalDateTime: ...
    def getDateTimeBefore(self) -> java.time.LocalDateTime: ...
    def getDuration(self) -> java.time.Duration: ...
    def getInstant(self) -> java.time.Instant: ...
    def getOffsetAfter(self) -> java.time.ZoneOffset: ...
    def getOffsetBefore(self) -> java.time.ZoneOffset: ...
    def hashCode(self) -> int: ...
    def isGap(self) -> bool: ...
    def isOverlap(self) -> bool: ...
    def isValidOffset(self, zoneOffset: java.time.ZoneOffset) -> bool: ...
    @staticmethod
    def of(localDateTime: java.time.LocalDateTime, zoneOffset: java.time.ZoneOffset, zoneOffset2: java.time.ZoneOffset) -> 'ZoneOffsetTransition': ...
    def toEpochSecond(self) -> int: ...
    def toString(self) -> str: ...

class ZoneOffsetTransitionRule(java.io.Serializable):
    def createTransition(self, int: int) -> ZoneOffsetTransition: ...
    def equals(self, object: typing.Any) -> bool: ...
    def getDayOfMonthIndicator(self) -> int: ...
    def getDayOfWeek(self) -> java.time.DayOfWeek: ...
    def getLocalTime(self) -> java.time.LocalTime: ...
    def getMonth(self) -> java.time.Month: ...
    def getOffsetAfter(self) -> java.time.ZoneOffset: ...
    def getOffsetBefore(self) -> java.time.ZoneOffset: ...
    def getStandardOffset(self) -> java.time.ZoneOffset: ...
    def getTimeDefinition(self) -> 'ZoneOffsetTransitionRule.TimeDefinition': ...
    def hashCode(self) -> int: ...
    def isMidnightEndOfDay(self) -> bool: ...
    @staticmethod
    def of(month: java.time.Month, int: int, dayOfWeek: java.time.DayOfWeek, localTime: java.time.LocalTime, boolean: bool, timeDefinition: 'ZoneOffsetTransitionRule.TimeDefinition', zoneOffset: java.time.ZoneOffset, zoneOffset2: java.time.ZoneOffset, zoneOffset3: java.time.ZoneOffset) -> 'ZoneOffsetTransitionRule': ...
    def toString(self) -> str: ...
    class TimeDefinition(java.lang.Enum['ZoneOffsetTransitionRule.TimeDefinition']):
        UTC: typing.ClassVar['ZoneOffsetTransitionRule.TimeDefinition'] = ...
        WALL: typing.ClassVar['ZoneOffsetTransitionRule.TimeDefinition'] = ...
        STANDARD: typing.ClassVar['ZoneOffsetTransitionRule.TimeDefinition'] = ...
        def createDateTime(self, localDateTime: java.time.LocalDateTime, zoneOffset: java.time.ZoneOffset, zoneOffset2: java.time.ZoneOffset) -> java.time.LocalDateTime: ...
        _valueOf_0__T = typing.TypeVar('_valueOf_0__T', bound=java.lang.Enum)  # <T>
        @typing.overload
        @staticmethod
        def valueOf(class_: typing.Type[_valueOf_0__T], string: str) -> _valueOf_0__T: ...
        @typing.overload
        @staticmethod
        def valueOf(string: str) -> 'ZoneOffsetTransitionRule.TimeDefinition': ...
        @staticmethod
        def values() -> typing.List['ZoneOffsetTransitionRule.TimeDefinition']: ...

class ZoneRules(java.io.Serializable):
    def equals(self, object: typing.Any) -> bool: ...
    def getDaylightSavings(self, instant: typing.Union[java.time.Instant, datetime.datetime]) -> java.time.Duration: ...
    @typing.overload
    def getOffset(self, instant: typing.Union[java.time.Instant, datetime.datetime]) -> java.time.ZoneOffset: ...
    @typing.overload
    def getOffset(self, localDateTime: java.time.LocalDateTime) -> java.time.ZoneOffset: ...
    def getStandardOffset(self, instant: typing.Union[java.time.Instant, datetime.datetime]) -> java.time.ZoneOffset: ...
    def getTransition(self, localDateTime: java.time.LocalDateTime) -> ZoneOffsetTransition: ...
    def getTransitionRules(self) -> java.util.List[ZoneOffsetTransitionRule]: ...
    def getTransitions(self) -> java.util.List[ZoneOffsetTransition]: ...
    def getValidOffsets(self, localDateTime: java.time.LocalDateTime) -> java.util.List[java.time.ZoneOffset]: ...
    def hashCode(self) -> int: ...
    def isDaylightSavings(self, instant: typing.Union[java.time.Instant, datetime.datetime]) -> bool: ...
    def isFixedOffset(self) -> bool: ...
    def isValidOffset(self, localDateTime: java.time.LocalDateTime, zoneOffset: java.time.ZoneOffset) -> bool: ...
    def nextTransition(self, instant: typing.Union[java.time.Instant, datetime.datetime]) -> ZoneOffsetTransition: ...
    @typing.overload
    @staticmethod
    def of(zoneOffset: java.time.ZoneOffset) -> 'ZoneRules': ...
    @typing.overload
    @staticmethod
    def of(zoneOffset: java.time.ZoneOffset, zoneOffset2: java.time.ZoneOffset, list: java.util.List[ZoneOffsetTransition], list2: java.util.List[ZoneOffsetTransition], list3: java.util.List[ZoneOffsetTransitionRule]) -> 'ZoneRules': ...
    def previousTransition(self, instant: typing.Union[java.time.Instant, datetime.datetime]) -> ZoneOffsetTransition: ...
    def toString(self) -> str: ...

class ZoneRulesException(java.time.DateTimeException):
    @typing.overload
    def __init__(self, string: str): ...
    @typing.overload
    def __init__(self, string: str, throwable: java.lang.Throwable): ...

class ZoneRulesProvider:
    @staticmethod
    def getAvailableZoneIds() -> java.util.Set[str]: ...
    @staticmethod
    def getRules(string: str, boolean: bool) -> ZoneRules: ...
    @staticmethod
    def getVersions(string: str) -> java.util.NavigableMap[str, ZoneRules]: ...
    @staticmethod
    def refresh() -> bool: ...
    @staticmethod
    def registerProvider(zoneRulesProvider: 'ZoneRulesProvider') -> None: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("java.time.zone")``.

    ZoneOffsetTransition: typing.Type[ZoneOffsetTransition]
    ZoneOffsetTransitionRule: typing.Type[ZoneOffsetTransitionRule]
    ZoneRules: typing.Type[ZoneRules]
    ZoneRulesException: typing.Type[ZoneRulesException]
    ZoneRulesProvider: typing.Type[ZoneRulesProvider]
