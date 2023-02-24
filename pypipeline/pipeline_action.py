from pypipeline.pipeline_item import PipelineItem


class PipelineAction:
    priority: int = 1
    abbrev: str | None = None

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


def get_parsable_actions(actions: list[PipelineAction]):
    """
    Returns a list of actions that can be parsed by the CLI.
    This is done by checking if the action has a parse method that returns something other than NotImplemented.
    """
    parsable = []
    for action in actions:
        try:
            if action.parse() is not NotImplemented:
                parsable.append(action)
        except NotImplementedError:
            continue
        except TypeError:
            parsable.append(action)
    return parsable


__all__ = ["PipelineAction", "get_parsable_actions"]
