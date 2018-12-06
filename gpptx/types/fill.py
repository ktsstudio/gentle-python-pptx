from abc import ABCMeta

from lxml.etree import ElementTree

from gpptx.types.color import Color
from gpptx.types.xml_node import XmlNode


class Fill(XmlNode, metaclass=ABCMeta):
    pass


class SolidFill(Fill):
    def __init__(self):
        super().__init__()
        raise NotImplementedError  # TODO

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError  # TODO

    @property
    def color(self) -> Color:
        raise NotImplementedError  # TODO


class GradientFill(Fill):
    def __init__(self):
        super().__init__()
        raise NotImplementedError  # TODO

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError  # TODO

    @property
    def path(self) -> object:
        raise NotImplementedError  # TODO
