import inspect
from typing import Any, Dict, Type

from objinspect import Class
from stdl.st import kebab_case

from pypipeline.item import Item


class Action:
    priority: int = 1
    abbrev: str | None = None
    type: str | None = None
    dict_exclude: list[str] = []
    allow_autoparse: bool = True

    def __init__(self) -> None:
        self.validate()

    @classmethod
    @property
    def name(cls):
        return kebab_case(cls.__name__)

    def dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "args": self.get_args(),
        }

    def get_args(self) -> Dict[str, Any]:
        cls = Class(self.__class__)
        init_args = cls.init_args
        args = {}
        if not init_args:
            return {}

        for i in init_args:
            if i.name in self.dict_exclude:
                continue
            args[i.name] = getattr(self, i.name)
        return args

    def __repr__(self):
        vars_str = ", ".join([f"{i}={j}" for i, j in vars(self).items()])
        return f"{self.__class__.__name__}({vars_str})"

    def __lt__(self, other):
        if isinstance(other, Action):
            return self.priority < other.priority
        raise NotImplementedError

    def validate(self) -> None:
        """
        Should raise an Error if the action is invalid.
        """
        return

    def process(self, item: Item) -> Item | bool:
        raise NotImplementedError

    def eval(self, item: Item) -> Item:
        raise NotImplementedError

    @classmethod
    def parse(cls, val: str | None = None) -> "Action":
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
    def get_docstring(cls) -> str:
        return inspect.getdoc(cls) or ""


class Modifier(Action):
    type = "modifier"

    def process(self, item: Item) -> Item:
        raise NotImplementedError

    def eval(self, item: Item) -> Item:
        return self.process(item)


class Filter(Action):
    type = "filter"
    dict_exclude: list[str] = ["invert"]

    def __init__(self, invert=False) -> None:
        self.invert = invert
        super().__init__()

    def eval(self, item: Item) -> Item:
        res = self.process(item)
        if self.invert:
            res = not res
        item.discarded = not res
        return item


def get_actions_dict(actions: list[Type[Action]]) -> dict[str, Type[Action]]:
    return {i.name: i for i in actions}


def parse_action(data: dict, actions: dict[str, Type[Action]]) -> Action:
    name = data["name"]
    if name not in actions:
        raise ValueError(f"Unknown action: '{name}'")
    cls = actions[name]
    return cls(**data["args"])


__all__ = ["Action", "Modifier", "Filter", "parse_action"]
