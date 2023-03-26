from typing import Any


class Item:
    def __init__(self) -> None:
        self.discarded = False
        self.extra: dict[str, Any] = {}

    def __repr__(self):
        return f"{self.__class__.__name__}(discarded={self.discarded})"

    def on_discard(self) -> None:
        return


__all__ = ["Item"]
