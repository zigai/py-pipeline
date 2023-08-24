import re
from fnmatch import fnmatch
from typing import Literal

from pypipeline.action import Filter
from pypipeline.constants import INT_MAX, INT_MIN, SEP
from pypipeline.util import get_pattern_type


class IntFilter(Filter):
    t = int

    def __init__(self, low=INT_MIN, high=INT_MAX, invert=False) -> None:
        self.low = low
        self.high = high
        super().__init__(invert)

    def validate(self):
        if self.low > self.high:
            raise ValueError

    @classmethod
    def parse(cls, val: str | None = None):
        if val is None or val == "":
            return cls()
        args = val.split(SEP)
        args = [i.strip() for i in args]
        if len(args) != 2:
            raise ValueError(args)
        match args:
            case ["", ""]:
                return cls()
            case [x, ""]:
                return cls(low=cls.t(x))
            case ["", x]:
                return cls(high=cls.t(x))
            case [x, y]:
                return cls(cls.t(x), cls.t(y))
            case _:
                raise ValueError(args)


class FloatFilter(IntFilter):
    t = float


class RegexFilter(Filter):
    def __init__(self, pattern: str | re.Pattern, invert=False) -> None:
        self.pattern = pattern
        if isinstance(self.pattern, str):
            self.pattern = re.compile(pattern)
        super().__init__(invert)

    def process(self, text: str) -> bool:
        return re.search(self.pattern, text) is not None

    @classmethod
    def parse(cls, val: str):
        return cls(val)


class GlobFilter(Filter):
    def __init__(self, pattern: str, invert=False) -> None:
        if pattern is None:
            raise ValueError
        self.pattern = pattern
        super().__init__(invert)

    def process(self, text: str) -> bool:
        return fnmatch(text, self.pattern)

    @classmethod
    def parse(cls, val: str):
        return cls(val)


class TextPatternFilter(Filter):
    """A filter that can be either a glob or regex pattern."""

    dict_exclude = ["t", "invert"]

    def __init__(
        self,
        pattern: str,
        invert=False,
        t: Literal["regex", "glob", None] = None,
    ) -> None:
        if t is None:
            t = get_pattern_type(pattern)
        if t is None:
            raise ValueError(f"'{pattern}' is not a valid glob or regex pattern.")
        if t == "regex":
            self.inner = RegexFilter(pattern, invert)
        elif t == "glob":
            self.inner = GlobFilter(pattern, invert)
        self.t = t
        self.pattern = pattern
        super().__init__(invert)

    def process(self, text: str) -> bool:
        return self.inner.process(text)

    @classmethod
    def parse(cls, val: str):
        return cls(val)


__all__ = [
    "Filter",
    "IntFilter",
    "FloatFilter",
    "RegexFilter",
    "GlobFilter",
]
