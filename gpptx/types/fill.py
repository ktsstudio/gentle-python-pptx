from abc import ABCMeta

from gpptx.types.color import Color


class Fill(metaclass=ABCMeta):
    def __init__(self):
        raise NotImplementedError


class SolidFill(Fill):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def color(self) -> Color:
        raise NotImplementedError


class GradientFill(Fill):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def path(self) -> object:  # TODO
        raise NotImplementedError
