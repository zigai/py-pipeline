import re
import sys
from fnmatch import fnmatch

from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem

INT_MAX = sys.maxsize
SEP = ":"


class Filter(PipelineAction):
    def process(self, item: PipelineItem) -> bool:
        ...

    def eval(self, item: PipelineItem) -> PipelineItem:
        item.discarded = self.process(item)
        return item


class IntFilter(Filter):
    t = int

    def __init__(self, low=0, high=INT_MAX) -> None:
        self.low = low
        self.high = high
        super().__init__()

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
    def __init__(self, pattern: str | re.Pattern) -> None:
        self.pattern = pattern
        if isinstance(self.pattern, str):
            self.pattern = re.compile(pattern)

    def process(self, text: str) -> bool:
        return re.search(self.pattern, text) is not None

    @classmethod
    def parse(cls, val: str):
        return cls(val)


class GlobFilter(Filter):
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def process(self, text: str) -> bool:
        return fnmatch(text, self.pattern)

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
