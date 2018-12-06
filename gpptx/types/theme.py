from typing import Dict

from lxml.etree import ElementTree

from gpptx.pptx_tools.colors import SYSTEM_COLOR_NAMES
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorators import cache_persist, CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slide import SlideMaster
from gpptx.types.xml_node import XmlNode


class Theme(CacheDecoratable, XmlNode):
    __slots__ = ('_xml_path', '_slide_master')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, xml_path: str, slide_master: SlideMaster):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._xml_path = xml_path
        self._slide_master = slide_master

    @property
    def xml(self) -> ElementTree:
        return self._storage.loader.get_file_xml(self._xml_path)

    @cache_persist
    @property
    def color_rgbs(self) -> Dict[str, str]:
        result: Dict[str, str] = dict()

        for elem in self.xml.xpath('a:themeElements/a:clrScheme/*', namespaces=pptx_xml_ns):
            standard_address_and_tag_name = str(elem.tag)
            tag_name = standard_address_and_tag_name.split('}')[1]
            color = elem[0].get('val')

            if color in SYSTEM_COLOR_NAMES.keys():
                color = SYSTEM_COLOR_NAMES[color]

            result[tag_name] = color

        color_map = self._slide_master.xml.xpath('p:clrMap[1]', namespaces=pptx_xml_ns)[0]
        result['bg1'] = result[color_map.attrib['bg1']]
        result['tx1'] = result[color_map.attrib['tx1']]
        result['bg2'] = result[color_map.attrib['bg2']]
        result['tx2'] = result[color_map.attrib['tx2']]

        return result
