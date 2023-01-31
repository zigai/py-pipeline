import multiprocessing

from stdl.lst import split
from tqdm import tqdm

from pypipeline.items_container import ItemsContainer
from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem


class Pipeline:
    def __init__(self, actions: list[PipelineAction] | None = None) -> None:
        self.actions: list[PipelineAction] = []
        if actions:
            self.actions.extend(actions)
        self.lock = multiprocessing.Manager().Lock()

    def add_action(self, action: PipelineAction):
        self.actions.append(action)

    def process_item(self, item: PipelineItem) -> PipelineItem:
        if item.discarded:
            return item
        for action in self.actions:
            item = action.eval(item)
            if item.discarded:
                return item
        return item

    def process_items(self, items: list, _pos: int = 0):
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

    def process_multi(self, items: list[PipelineItem], t: int):
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
                    self.process_items,
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

    def __init__(self, actions: list[PipelineAction] | None = None) -> None:
        super().__init__(actions)
        self.actions.sort()

    def add_action(self, action: PipelineAction):
        super().add_action(action)
        self.actions.sort()


__all__ = ["Pipeline", "PriorityPipeline"]
