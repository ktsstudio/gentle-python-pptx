import re
from typing import List, Optional

from lxml.etree import ElementTree

from gpptx.pptx_tools.paths import SLIDES_PATH_PREFIX_WITH_FILE, PRESENTATION_PATH
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_persist_property, cache_local_property
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slides_coll import SlidesCollection
from gpptx.types.units import Emu
from gpptx.types.xml_node import CacheDecoratableXmlNode
from gpptx.util.list import first_or_none


class Presentation(CacheDecoratableXmlNode):
    _SLIDE_ID_REGEX = re.compile(r'ppt/slides/slide(\d+).xml')

    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey):
        super().__init__(storage, cache_key)

    @property
    def xml(self) -> ElementTree:
        return self._storage.loader.get_file_xml(PRESENTATION_PATH)

    def save_xml(self) -> None:
        return self._storage.loader.save_file_xml(PRESENTATION_PATH, self.xml)

    @property
    def slides(self) -> SlidesCollection:
        return SlidesCollection(self._storage, self._storage_cache_key.make_son('slides'), self, self._slide_paths)

    @cache_persist_property
    def slide_width(self) -> Optional[Emu]:
        if self._sld_sz is not None:
            return Emu(self._sld_sz.get('cx'))
        if self.do_use_defaults_when_null:
            return self._default_slide_width
        return None

    @property
    def _default_slide_width(self) -> Emu:
        return Emu(0)

    @slide_width.serializer
    def slide_width(self, v: Emu) -> int:
        return int(v)

    @slide_width.unserializer
    def slide_width(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def slide_height(self) -> Optional[Emu]:
        if self._sld_sz is not None:
            return Emu(self._sld_sz.get('cy'))
        if self.do_use_defaults_when_null:
            return self._default_slide_height
        return None

    @property
    def _default_slide_height(self) -> Emu:
        return Emu(0)

    @slide_height.serializer
    def slide_height(self, v: Emu) -> int:
        return int(v)

    @slide_height.unserializer
    def slide_height(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def _slide_paths(self) -> List[str]:
        paths = [path for path in self._storage.loader.get_filelist() if path.startswith(SLIDES_PATH_PREFIX_WITH_FILE)]
        paths.sort(key=lambda it: int(self._SLIDE_ID_REGEX.match(it)[1]))
        return paths

    @cache_local_property
    def _sld_sz(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('p:sldSz[1]', namespaces=pptx_xml_ns))
