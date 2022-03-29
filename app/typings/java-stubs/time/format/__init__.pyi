import java.lang
import java.text
import java.time
import java.time.chrono
import java.time.temporal
import java.util
import typing



class DateTimeFormatter:
    ISO_LOCAL_DATE: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_OFFSET_DATE: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_DATE: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_LOCAL_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_OFFSET_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_LOCAL_DATE_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_OFFSET_DATE_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_ZONED_DATE_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_DATE_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_ORDINAL_DATE: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_WEEK_DATE: typing.ClassVar['DateTimeFormatter'] = ...
    ISO_INSTANT: typing.ClassVar['DateTimeFormatter'] = ...
    BASIC_ISO_DATE: typing.ClassVar['DateTimeFormatter'] = ...
    RFC_1123_DATE_TIME: typing.ClassVar['DateTimeFormatter'] = ...
    def format(self, temporalAccessor: java.time.temporal.TemporalAccessor) -> str: ...
    def formatTo(self, temporalAccessor: java.time.temporal.TemporalAccessor, appendable: java.lang.Appendable) -> None: ...
    def getChronology(self) -> java.time.chrono.Chronology: ...
    def getDecimalStyle(self) -> 'DecimalStyle': ...
    def getLocale(self) -> java.util.Locale: ...
    def getResolverFields(self) -> java.util.Set[java.time.temporal.TemporalField]: ...
    def getResolverStyle(self) -> 'ResolverStyle': ...
    def getZone(self) -> java.time.ZoneId: ...
    def localizedBy(self, locale: java.util.Locale) -> 'DateTimeFormatter': ...
    @staticmethod
    def ofLocalizedDate(formatStyle: 'FormatStyle') -> 'DateTimeFormatter': ...
    @typing.overload
    @staticmethod
    def ofLocalizedDateTime(formatStyle: 'FormatStyle') -> 'DateTimeFormatter': ...
    @typing.overload
    @staticmethod
    def ofLocalizedDateTime(formatStyle: 'FormatStyle', formatStyle2: 'FormatStyle') -> 'DateTimeFormatter': ...
    @staticmethod
    def ofLocalizedTime(formatStyle: 'FormatStyle') -> 'DateTimeFormatter': ...
    @typing.overload
    @staticmethod
    def ofPattern(string: str) -> 'DateTimeFormatter': ...
    @typing.overload
    @staticmethod
    def ofPattern(string: str, locale: java.util.Locale) -> 'DateTimeFormatter': ...
    _parse_0__T = typing.TypeVar('_parse_0__T')  # <T>
    @typing.overload
    def parse(self, charSequence: typing.Union[java.lang.CharSequence, str], temporalQuery: typing.Union[java.time.temporal.TemporalQuery[_parse_0__T], typing.Callable[[java.time.temporal.TemporalAccessor], _parse_0__T]]) -> _parse_0__T: ...
    @typing.overload
    def parse(self, charSequence: typing.Union[java.lang.CharSequence, str]) -> java.time.temporal.TemporalAccessor: ...
    @typing.overload
    def parse(self, charSequence: typing.Union[java.lang.CharSequence, str], parsePosition: java.text.ParsePosition) -> java.time.temporal.TemporalAccessor: ...
    def parseBest(self, charSequence: typing.Union[java.lang.CharSequence, str], temporalQueryArray: typing.List[java.time.temporal.TemporalQuery[typing.Any]]) -> java.time.temporal.TemporalAccessor: ...
    def parseUnresolved(self, charSequence: typing.Union[java.lang.CharSequence, str], parsePosition: java.text.ParsePosition) -> java.time.temporal.TemporalAccessor: ...
    @staticmethod
    def parsedExcessDays() -> java.time.temporal.TemporalQuery[java.time.Period]: ...
    @staticmethod
    def parsedLeapSecond() -> java.time.temporal.TemporalQuery[bool]: ...
    @typing.overload
    def toFormat(self) -> java.text.Format: ...
    @typing.overload
    def toFormat(self, temporalQuery: typing.Union[java.time.temporal.TemporalQuery[typing.Any], typing.Callable[[java.time.temporal.TemporalAccessor], typing.Any]]) -> java.text.Format: ...
    def toString(self) -> str: ...
    def withChronology(self, chronology: java.time.chrono.Chronology) -> 'DateTimeFormatter': ...
    def withDecimalStyle(self, decimalStyle: 'DecimalStyle') -> 'DateTimeFormatter': ...
    def withLocale(self, locale: java.util.Locale) -> 'DateTimeFormatter': ...
    @typing.overload
    def withResolverFields(self, temporalFieldArray: typing.List[java.time.temporal.TemporalField]) -> 'DateTimeFormatter': ...
    @typing.overload
    def withResolverFields(self, set: java.util.Set[java.time.temporal.TemporalField]) -> 'DateTimeFormatter': ...
    def withResolverStyle(self, resolverStyle: 'ResolverStyle') -> 'DateTimeFormatter': ...
    def withZone(self, zoneId: java.time.ZoneId) -> 'DateTimeFormatter': ...

class DateTimeFormatterBuilder:
    def __init__(self): ...
    def append(self, dateTimeFormatter: DateTimeFormatter) -> 'DateTimeFormatterBuilder': ...
    def appendChronologyId(self) -> 'DateTimeFormatterBuilder': ...
    def appendChronologyText(self, textStyle: 'TextStyle') -> 'DateTimeFormatterBuilder': ...
    def appendFraction(self, temporalField: java.time.temporal.TemporalField, int: int, int2: int, boolean: bool) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendGenericZoneText(self, textStyle: 'TextStyle') -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendGenericZoneText(self, textStyle: 'TextStyle', set: java.util.Set[java.time.ZoneId]) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendInstant(self) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendInstant(self, int: int) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendLiteral(self, char: str) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendLiteral(self, string: str) -> 'DateTimeFormatterBuilder': ...
    def appendLocalized(self, formatStyle: 'FormatStyle', formatStyle2: 'FormatStyle') -> 'DateTimeFormatterBuilder': ...
    def appendLocalizedOffset(self, textStyle: 'TextStyle') -> 'DateTimeFormatterBuilder': ...
    def appendOffset(self, string: str, string2: str) -> 'DateTimeFormatterBuilder': ...
    def appendOffsetId(self) -> 'DateTimeFormatterBuilder': ...
    def appendOptional(self, dateTimeFormatter: DateTimeFormatter) -> 'DateTimeFormatterBuilder': ...
    def appendPattern(self, string: str) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendText(self, temporalField: java.time.temporal.TemporalField) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendText(self, temporalField: java.time.temporal.TemporalField, textStyle: 'TextStyle') -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendText(self, temporalField: java.time.temporal.TemporalField, map: typing.Union[java.util.Map[int, str], typing.Mapping[int, str]]) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendValue(self, temporalField: java.time.temporal.TemporalField) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendValue(self, temporalField: java.time.temporal.TemporalField, int: int) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendValue(self, temporalField: java.time.temporal.TemporalField, int: int, int2: int, signStyle: 'SignStyle') -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendValueReduced(self, temporalField: java.time.temporal.TemporalField, int: int, int2: int, int3: int) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendValueReduced(self, temporalField: java.time.temporal.TemporalField, int: int, int2: int, chronoLocalDate: java.time.chrono.ChronoLocalDate) -> 'DateTimeFormatterBuilder': ...
    def appendZoneId(self) -> 'DateTimeFormatterBuilder': ...
    def appendZoneOrOffsetId(self) -> 'DateTimeFormatterBuilder': ...
    def appendZoneRegionId(self) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendZoneText(self, textStyle: 'TextStyle') -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def appendZoneText(self, textStyle: 'TextStyle', set: java.util.Set[java.time.ZoneId]) -> 'DateTimeFormatterBuilder': ...
    @staticmethod
    def getLocalizedDateTimePattern(formatStyle: 'FormatStyle', formatStyle2: 'FormatStyle', chronology: java.time.chrono.Chronology, locale: java.util.Locale) -> str: ...
    def optionalEnd(self) -> 'DateTimeFormatterBuilder': ...
    def optionalStart(self) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def padNext(self, int: int) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def padNext(self, int: int, char: str) -> 'DateTimeFormatterBuilder': ...
    def parseCaseInsensitive(self) -> 'DateTimeFormatterBuilder': ...
    def parseCaseSensitive(self) -> 'DateTimeFormatterBuilder': ...
    def parseDefaulting(self, temporalField: java.time.temporal.TemporalField, long: int) -> 'DateTimeFormatterBuilder': ...
    def parseLenient(self) -> 'DateTimeFormatterBuilder': ...
    def parseStrict(self) -> 'DateTimeFormatterBuilder': ...
    @typing.overload
    def toFormatter(self) -> DateTimeFormatter: ...
    @typing.overload
    def toFormatter(self, locale: java.util.Locale) -> DateTimeFormatter: ...

class DateTimeParseException(java.time.DateTimeException):
    @typing.overload
    def __init__(self, string: str, charSequence: typing.Union[java.lang.CharSequence, str], int: int): ...
    @typing.overload
    def __init__(self, string: str, charSequence: typing.Union[java.lang.CharSequence, str], int: int, throwable: java.lang.Throwable): ...
    def getErrorIndex(self) -> int: ...
    def getParsedString(self) -> str: ...

class DecimalStyle:
    STANDARD: typing.ClassVar['DecimalStyle'] = ...
    def equals(self, object: typing.Any) -> bool: ...
    @staticmethod
    def getAvailableLocales() -> java.util.Set[java.util.Locale]: ...
    def getDecimalSeparator(self) -> str: ...
    def getNegativeSign(self) -> str: ...
    def getPositiveSign(self) -> str: ...
    def getZeroDigit(self) -> str: ...
    def hashCode(self) -> int: ...
    @staticmethod
    def of(locale: java.util.Locale) -> 'DecimalStyle': ...
    @staticmethod
    def ofDefaultLocale() -> 'DecimalStyle': ...
    def toString(self) -> str: ...
    def withDecimalSeparator(self, char: str) -> 'DecimalStyle': ...
    def withNegativeSign(self, char: str) -> 'DecimalStyle': ...
    def withPositiveSign(self, char: str) -> 'DecimalStyle': ...
    def withZeroDigit(self, char: str) -> 'DecimalStyle': ...

class FormatStyle(java.lang.Enum['FormatStyle']):
    FULL: typing.ClassVar['FormatStyle'] = ...
    LONG: typing.ClassVar['FormatStyle'] = ...
    MEDIUM: typing.ClassVar['FormatStyle'] = ...
    SHORT: typing.ClassVar['FormatStyle'] = ...
    _valueOf_0__T = typing.TypeVar('_valueOf_0__T', bound=java.lang.Enum)  # <T>
    @typing.overload
    @staticmethod
    def valueOf(class_: typing.Type[_valueOf_0__T], string: str) -> _valueOf_0__T: ...
    @typing.overload
    @staticmethod
    def valueOf(string: str) -> 'FormatStyle': ...
    @staticmethod
    def values() -> typing.List['FormatStyle']: ...

class ResolverStyle(java.lang.Enum['ResolverStyle']):
    STRICT: typing.ClassVar['ResolverStyle'] = ...
    SMART: typing.ClassVar['ResolverStyle'] = ...
    LENIENT: typing.ClassVar['ResolverStyle'] = ...
    _valueOf_0__T = typing.TypeVar('_valueOf_0__T', bound=java.lang.Enum)  # <T>
    @typing.overload
    @staticmethod
    def valueOf(class_: typing.Type[_valueOf_0__T], string: str) -> _valueOf_0__T: ...
    @typing.overload
    @staticmethod
    def valueOf(string: str) -> 'ResolverStyle': ...
    @staticmethod
    def values() -> typing.List['ResolverStyle']: ...

class SignStyle(java.lang.Enum['SignStyle']):
    NORMAL: typing.ClassVar['SignStyle'] = ...
    ALWAYS: typing.ClassVar['SignStyle'] = ...
    NEVER: typing.ClassVar['SignStyle'] = ...
    NOT_NEGATIVE: typing.ClassVar['SignStyle'] = ...
    EXCEEDS_PAD: typing.ClassVar['SignStyle'] = ...
    _valueOf_0__T = typing.TypeVar('_valueOf_0__T', bound=java.lang.Enum)  # <T>
    @typing.overload
    @staticmethod
    def valueOf(class_: typing.Type[_valueOf_0__T], string: str) -> _valueOf_0__T: ...
    @typing.overload
    @staticmethod
    def valueOf(string: str) -> 'SignStyle': ...
    @staticmethod
    def values() -> typing.List['SignStyle']: ...

class TextStyle(java.lang.Enum['TextStyle']):
    FULL: typing.ClassVar['TextStyle'] = ...
    FULL_STANDALONE: typing.ClassVar['TextStyle'] = ...
    SHORT: typing.ClassVar['TextStyle'] = ...
    SHORT_STANDALONE: typing.ClassVar['TextStyle'] = ...
    NARROW: typing.ClassVar['TextStyle'] = ...
    NARROW_STANDALONE: typing.ClassVar['TextStyle'] = ...
    def asNormal(self) -> 'TextStyle': ...
    def asStandalone(self) -> 'TextStyle': ...
    def isStandalone(self) -> bool: ...
    _valueOf_0__T = typing.TypeVar('_valueOf_0__T', bound=java.lang.Enum)  # <T>
    @typing.overload
    @staticmethod
    def valueOf(class_: typing.Type[_valueOf_0__T], string: str) -> _valueOf_0__T: ...
    @typing.overload
    @staticmethod
    def valueOf(string: str) -> 'TextStyle': ...
    @staticmethod
    def values() -> typing.List['TextStyle']: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("java.time.format")``.

    DateTimeFormatter: typing.Type[DateTimeFormatter]
    DateTimeFormatterBuilder: typing.Type[DateTimeFormatterBuilder]
    DateTimeParseException: typing.Type[DateTimeParseException]
    DecimalStyle: typing.Type[DecimalStyle]
    FormatStyle: typing.Type[FormatStyle]
    ResolverStyle: typing.Type[ResolverStyle]
    SignStyle: typing.Type[SignStyle]
    TextStyle: typing.Type[TextStyle]