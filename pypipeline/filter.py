import sys

from pipeline_action import PipelineAction
from pipeline_item import PipelineItem

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
