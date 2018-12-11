from abc import ABC
from contextlib import contextmanager

from lxml import etree
from lxml.etree import ElementTree

from gpptx.storage.cache.decorator import CacheDecoratable


class BaseXmlNode(ABC):
    __slots__ = ()

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError

    @property
    def xml_str(self) -> str:
        return etree.tostring(self.xml).decode('utf-8')

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def do_use_defaults_when_null(self) -> bool:
        raise NotImplementedError

    @do_use_defaults_when_null.setter
    def do_use_defaults_when_null(self, value: bool) -> None:
        raise NotImplementedError

    @contextmanager
    def with_turned_off_defaults_when_null(self):
        old_state = self.do_use_defaults_when_null
        self.do_use_defaults_when_null = False
        try:
            yield
        finally:
            # noinspection PyAttributeOutsideInit
            # because of Pycharm internal error
            self.do_use_defaults_when_null = old_state

    @contextmanager
    def with_turned_on_defaults_when_null(self):
        old_state = self.do_use_defaults_when_null
        self.do_use_defaults_when_null = True
        try:
            yield
        finally:
            # noinspection PyAttributeOutsideInit
            # because of Pycharm internal error
            self.do_use_defaults_when_null = old_state


class XmlNode(BaseXmlNode, ABC):
    __slots__ = ('_do_use_defaults_when_null',)

    def __init__(self):
        self._do_use_defaults_when_null = True

    @property
    def do_use_defaults_when_null(self) -> bool:
        return self._do_use_defaults_when_null

    @do_use_defaults_when_null.setter
    def do_use_defaults_when_null(self, value: bool) -> None:
        self._do_use_defaults_when_null = value


class CacheDecoratableXmlNode(BaseXmlNode, CacheDecoratable, ABC):
    __slots__ = ('_do_use_defaults_when_null',)

    def __init__(self):
        self._do_use_defaults_when_null = True

    @property
    def do_use_defaults_when_null(self) -> bool:
        return self._do_use_defaults_when_null

    @do_use_defaults_when_null.setter
    def do_use_defaults_when_null(self, value: bool) -> None:
        self._do_use_defaults_when_null = value
        if self._do_use_defaults_when_null:
            self._storage_cache_key.postfix = None
        else:
            self._storage_cache_key.postfix = 'disabled_defaults_when_null'
