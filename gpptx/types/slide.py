from abc import ABC
from typing import List

from lxml.etree import ElementTree

from gpptx.pptx_tools.paths import make_rels_path, SLIDE_LAYOUTS_PATH_PREFIX, \
    SLIDE_MASTERS_PATH_PREFIX, THEMES_PATH_PREFIX
from gpptx.pptx_tools.rels import find_first_relation_path_with_prefix
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_persist_property, help_lazy_list_property, help_lazy_property
from gpptx.storage.cache.lazy import LazyList, Lazy, LazyByFunction
from gpptx.storage.storage import PresentationStorage
from gpptx.types.shapes_coll import ShapesCollection
from gpptx.types.theme import Theme
from gpptx.types.xml_node import CacheDecoratableXmlNode
from gpptx.util.list import first_or_none


class SlideLike(CacheDecoratableXmlNode, ABC):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key

    @property
    def shapes(self) -> ShapesCollection:
        return ShapesCollection(self._storage, self._storage_cache_key.make_son('shapes'),
                                self._shape_xmls, self.shapes_root_getter, self)

    @property
    def theme(self) -> Theme:
        raise NotImplementedError

    @help_lazy_list_property
    def _shape_xmls(self) -> LazyList:
        def find() -> List[ElementTree]:
            els = self.xml.xpath('p:cSld[1]/p:spTree[1]/*', namespaces=pptx_xml_ns)

            els_at_indexes_to_remove = list()
            for i, el in enumerate(els):
                if el.tag.endswith('Pr'):
                    els_at_indexes_to_remove.append(i)
            delete_shift = 0
            for i in els_at_indexes_to_remove:
                els.pop(i - delete_shift)
                delete_shift += 1

            return els

        return LazyList(find)

    @help_lazy_property
    def shapes_root_getter(self) -> Lazy:
        def find():
            return first_or_none(self.xml.xpath('p:cSld[1]/p:spTree[1]', namespaces=pptx_xml_ns))

        return LazyByFunction(find)


class SlideMaster(SlideLike):
    __slots__ = ('_xml_path',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, xml_path: str):
        super().__init__(storage, cache_key)
        self._storage = storage
        self._storage_cache_key = cache_key
        self._xml_path = xml_path

    @property
    def xml(self) -> ElementTree:
        return self._storage.loader.get_file_xml(self._xml_path)

    def save_xml(self) -> None:
        return self._storage.loader.save_file_xml(self._xml_path, self.xml)

    @property
    def theme(self) -> Theme:
        return Theme(self._storage,
                     self._storage_cache_key.make_son('theme').make_son(self._theme_path),
                     self._theme_path,
                     self)

    @cache_persist_property
    def _theme_path(self) -> str:
        rels_path = make_rels_path(self._xml_path)
        return find_first_relation_path_with_prefix(self._storage.loader, rels_path, THEMES_PATH_PREFIX)


class SlideLayout(SlideLike):
    __slots__ = ('_xml_path',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, xml_path: str):
        super().__init__(storage, cache_key)
        self._storage = storage
        self._storage_cache_key = cache_key
        self._xml_path = xml_path

    @property
    def xml(self) -> ElementTree:
        return self._storage.loader.get_file_xml(self._xml_path)

    def save_xml(self) -> None:
        return self._storage.loader.save_file_xml(self._xml_path, self.xml)

    @property
    def slide_master(self) -> SlideMaster:
        return SlideMaster(self._storage,
                           self._storage_cache_key.root.make_son('slide_master').make_son(self._slide_master_path),
                           self._slide_master_path)

    @property
    def theme(self) -> Theme:
        return self.slide_master.theme

    @cache_persist_property
    def _slide_master_path(self) -> str:
        rels_path = make_rels_path(self._xml_path)
        return find_first_relation_path_with_prefix(self._storage.loader, rels_path, SLIDE_MASTERS_PATH_PREFIX)


class Slide(SlideLike):
    __slots__ = ('_xml_path',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, xml_path: str):
        super().__init__(storage, cache_key)
        self._storage = storage
        self._storage_cache_key = cache_key
        self._xml_path = xml_path

    @property
    def xml(self) -> ElementTree:
        return self._storage.loader.get_file_xml(self._xml_path)

    def save_xml(self) -> None:
        return self._storage.loader.save_file_xml(self._xml_path, self.xml)

    @property
    def slide_layout(self) -> SlideLayout:
        return SlideLayout(self._storage,
                           self._storage_cache_key.root.make_son('slide_layout').make_son(self._slide_layout_path),
                           self._slide_layout_path)

    @property
    def theme(self) -> Theme:
        return self.slide_layout.theme

    @cache_persist_property
    def _slide_layout_path(self) -> str:
        rels_path = make_rels_path(self._xml_path)
        return find_first_relation_path_with_prefix(self._storage.loader, rels_path, SLIDE_LAYOUTS_PATH_PREFIX)
