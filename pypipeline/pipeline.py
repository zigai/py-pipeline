import multiprocessing

from stdl.lst import split
from tqdm import tqdm

from pypipeline.action import Action
from pypipeline.item import Item
from pypipeline.items_container import ItemsContainer


class Pipeline:
    def __init__(self, actions: list[Action] | None = None, on_discrad=True, verbose=False) -> None:
        self.actions: list[Action] = []
        if actions:
            self.actions.extend(actions)
        self.lock = multiprocessing.Manager().Lock()
        self.on_discard = on_discrad
        self.verbose = verbose
        if not self.verbose:
            self.process = self.process_no_bar

    def add_action(self, action: Action):
        self.actions.append(action)

    def process_item(self, item: Item) -> Item:
        if item.discarded:
            return item
        for action in self.actions:
            item = action.eval(item)
            if item.discarded:
                if self.on_discard:
                    item.on_discard()
                return item
        return item

    def process(self, items: list, _pos: int = 0):
        """
        Process a list of items through the pipeline.

        Args:
            items (list): A list of items to be processed.
            _pos (int, optional): The position of the progress bar. Don't modify, only used for process_multi.

        Returns:
            ItemsContainer: A container of processed items.

        """
        with self.lock:
            bar = tqdm(desc=f"[{_pos+1}]", total=len(items), position=_pos, leave=True)
        results = []
        for item in items:
            results.append(self.process_item(item))
            with self.lock:
                bar.update(1)
        return ItemsContainer(results)

    def process_no_bar(self, items: list, _pos: int = 0):
        """
        Same as process, but without a progress bar.
        """
        return ItemsContainer([self.process_item(item) for item in items])

    def process_multi(self, items: list[Item], t: int):
        """
        Process a list of items in parallel using multiple threads.

        Args:
            items (list[PipelineItem]): A list of items to be processed.
            t (int): The number of threads to use for processing.

        Returns:
            ItemsContainer: A container of processed items.

        """
        pool = multiprocessing.Pool(t)
        list_chunks = split(items, t)
        rvals = []
        for pos, chunk in enumerate(list_chunks):
            rvals.append(
                pool.apply_async(
                    self.process,
                    args=(chunk, pos),
                )
            )
        results = []
        for chunk in rvals:
            results.extend(chunk.get())
        return ItemsContainer(results)

    def print_actions(self):
        print("Pipeline actions:")
        for i in self.actions:
            print(f"\t{i}")


class PriorityPipeline(Pipeline):
    """
    A subclass of Pipeline that sorts the pipeline actions by priority
    """

    def __init__(self, actions: list[Action] | None = None) -> None:
        super().__init__(actions)
        self.actions.sort()

    def add_action(self, action: Action):
        super().add_action(action)
        self.actions.sort()


__all__ = ["Pipeline", "PriorityPipeline"]
