import pprint

from pipeline_item import PipelineItem


class ItemsContainer:
    def __init__(self, items: list[PipelineItem] | None = None) -> None:
        self.items: list[PipelineItem] = []
        if items:
            self.items.extend(items)

    def add(self, item: PipelineItem):
        self.items.append(item)

    def remove(self, item: PipelineItem):
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
