class PipelineItem:
    def __init__(self) -> None:
        self.discarded = False

    def __repr__(self):
        return f"{self.__class__.__name__}(discarded={self.discarded})"


__all__ = ["PipelineItem"]
