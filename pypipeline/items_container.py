import pprint

from pypipeline.item import Item


class ItemsContainer:
    def __init__(self, items: list[Item] | None = None) -> None:
        self.items: list[Item] = items or []

    def add(self, item: Item):
        self.items.append(item)

    def remove(self, item: Item):
        self.items.remove(item)

    def __iter__(self):
        for i in self.items:
            yield i

    @property
    def discarded(self):
        return [i for i in self.items if i.discarded]

    @property
    def kept(self):
        return [i for i in self.items if not i.discarded]

    def invert_discarded(self):
        for i in self.items:
            i.discarded = not i.discarded

    def remove_discarded(self):
        self.items = self.kept

    def print(self):
        pprint.pprint(self.items)


__all__ = ["ItemsContainer"]
