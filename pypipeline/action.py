import inspect

from pypipeline.item import Item


class Action:
    priority: int = 1
    abbrev: str | None = None
    type: str | None = None

    def __init__(self) -> None:
        self.validate()

    def __repr__(self):
        vars_str = ", ".join([f"{i}={j}" for i, j in vars(self).items()])
        return f"{self.__class__.__name__}({vars_str})"

    def __lt__(self, other):
        if isinstance(other, Action):
            return self.priority < other.priority
        return NotImplemented

    @classmethod
    def is_parsable(cls):
        try:
            if cls.parse() is NotImplemented:
                return False
            return True
        except NotImplementedError:
            return False
        except TypeError:
            return True

    @classmethod
    def get_docstr(cls) -> str:
        return inspect.getdoc(cls) or ""

    def process(self, item: Item) -> Item | bool:
        return NotImplemented

    def eval(self, item: Item) -> Item:
        return NotImplemented

    @classmethod
    def parse(cls, val: str | None = None) -> "Action":
        return NotImplemented

    def validate(self) -> None:
        return


__all__ = ["Action"]
