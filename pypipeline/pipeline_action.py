from pypipeline.pipeline_item import PipelineItem


class PipelineAction:
    priority: int = 1

    def __init__(self) -> None:
        self.validate_args()

    def __repr__(self):
        vars_str = ", ".join([f"{i}={j}" for i, j in vars(self).items()])
        return f"{self.__class__.__name__}({vars_str})"

    def __lt__(self, other):
        if isinstance(other, PipelineAction):
            return self.priority < other.priority
        return NotImplemented

    def process(self, item: PipelineItem) -> PipelineItem | bool:
        ...

    def eval(self, item: PipelineItem) -> PipelineItem:
        ...

    @classmethod
    def parse(cls, val: str | None = None):
        return NotImplemented

    def validate_args(self) -> None:
        return


__all__ = ["PipelineAction"]
