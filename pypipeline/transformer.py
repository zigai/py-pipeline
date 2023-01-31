from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem


class Transformer(PipelineAction):
    def process(self, item: PipelineItem) -> PipelineItem:
        ...


__all__ = ["Transformer"]
