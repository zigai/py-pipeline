from pipeline_item import PipelineItem
from pipeline_action import PipelineAction


class Transformer(PipelineAction):
    def process(self, item: PipelineItem) -> PipelineItem:
        ...
