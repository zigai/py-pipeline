from pypipeline.constants import SEP
from pypipeline.pipeline_action import PipelineAction
from pypipeline.pipeline_item import PipelineItem


class Transformer(PipelineAction):
    def process(self, item: PipelineItem) -> PipelineItem:
        return NotImplemented


__all__ = ["Transformer"]
