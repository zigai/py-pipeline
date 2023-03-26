from pypipeline.action import Action
from pypipeline.constants import SEP
from pypipeline.item import Item


class Transformer(Action):
    type = "transformer"

    def process(self, item: Item) -> Item:
        return NotImplemented


__all__ = ["Transformer"]
