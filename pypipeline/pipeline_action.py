import inspect

import docstring_parser

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
        return NotImplemented

    def eval(self, item: PipelineItem) -> PipelineItem:
        return NotImplemented

    @classmethod
    def parse(cls, val: str | None = None):
        return NotImplemented

    def validate_args(self) -> None:
        return


def get_parsable_actions(actions: list[PipelineAction]) -> list[PipelineAction]:
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


def get_action_description(action: PipelineAction):
    doc = inspect.getdoc(action)
    if doc is None:
        return ""
    doc = docstring_parser.parse(doc)
    if doc.short_description:
        return doc.short_description
    if doc.long_description:
        return doc.long_description
    return ""


__all__ = ["PipelineAction", "get_parsable_actions"]
