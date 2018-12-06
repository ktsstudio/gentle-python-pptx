from abc import ABCMeta
from typing import Callable

from lxml.etree import ElementTree


class XmlNode(metaclass=ABCMeta):
    __slots__ = ('do_use_defaults_when_null',)

    def __init__(self):
        self.do_use_defaults_when_null = True

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError

    @property
    def xml_getter(self) -> Callable[[], ElementTree]:
        return lambda: self.xml
