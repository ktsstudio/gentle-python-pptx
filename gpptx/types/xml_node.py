from abc import ABC
from contextlib import contextmanager

from lxml.etree import ElementTree

from gpptx.storage.cache.decorators import CacheDecoratable


class BaseXmlNode(ABC):
    __slots__ = ()

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError

    def save_xml(self) -> None:
        raise NotImplementedError


# workaround because multiple inheritance with slots is prohibited in Python
class _XmlNodeMethods:
    __slots__ = ()
    # __slots__ = ('do_use_defaults_when_null',)

    # noinspection PyDunderSlots,PyAttributeOutsideInit,PyUnresolvedReferences
    @contextmanager
    def with_turned_off_defaults_when_null(self):
        old_state = self.do_use_defaults_when_null
        self.do_use_defaults_when_null = False
        try:
            yield
        finally:
            self.do_use_defaults_when_null = old_state

    # noinspection PyDunderSlots,PyAttributeOutsideInit,PyUnresolvedReferences
    @contextmanager
    def with_turned_on_defaults_when_null(self):
        old_state = self.do_use_defaults_when_null
        self.do_use_defaults_when_null = True
        try:
            yield
        finally:
            self.do_use_defaults_when_null = old_state


class XmlNode(BaseXmlNode, _XmlNodeMethods, ABC):
    __slots__ = ('do_use_defaults_when_null',)

    def __init__(self):
        self.do_use_defaults_when_null = True


# workaround because multiple inheritance with slots is prohibited in Python
class CacheDecoratableXmlNode(BaseXmlNode, CacheDecoratable, _XmlNodeMethods, ABC):
    __slots__ = ('do_use_defaults_when_null',)

    def __init__(self):
        self.do_use_defaults_when_null = True
