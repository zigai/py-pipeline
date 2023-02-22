import re
import sys
from fnmatch import fnmatch

from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem
from pypipeline.util import get_pattern_type

INT_MAX = sys.maxsize
INT_MIN = -INT_MAX - 1
SEP = ":"


class Filter(PipelineAction):
    def __init__(self, invert=False) -> None:
        self.invert = invert
        super().__init__()

    def process(self, item: PipelineItem) -> bool:
        return NotImplemented

    def eval(self, item: PipelineItem) -> PipelineItem:
        res = self.process(item)
        if self.invert:
            res = not res
        item.discarded = not res
        return item


class IntFilter(Filter):
    t = int

    def __init__(self, low=INT_MIN, high=INT_MAX, invert=False) -> None:
        self.low = low
        self.high = high
        super().__init__(invert)

    def validate_args(self):
        if self.low > self.high:
            raise ValueError

    @classmethod
    def parse(cls, val: str | None = None):
        if val is None or val == "":
            return cls()
        args = val.split(SEP)
        args = [i.strip() for i in args]
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

    def __init__(self, pattern: str, invert=False, pattern_type=None) -> None:
        if pattern_type is None:
            pattern_type = get_pattern_type(pattern)
        if pattern_type is None:
            raise ValueError(f"'{pattern}' is not a valid glob or regex pattern.")
        if pattern_type == "regex":
            self.inner = RegexFilter(pattern, invert)
        elif pattern_type == "glob":
            self.inner = GlobFilter(pattern, invert)
        self.pattern_type = pattern_type
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
