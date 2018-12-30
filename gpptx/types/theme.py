from typing import Dict

from lxml.etree import ElementTree

from gpptx.pptx_tools.colors import SYSTEM_COLOR_NAMES
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_persist_property
from gpptx.storage.storage import PresentationStorage
from gpptx.types.xml_node import CacheDecoratableXmlNode


class Theme(CacheDecoratableXmlNode):
    __slots__ = ('_xml_path', '_slide_master')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, xml_path: str, slide_master):
        from gpptx.types.slide import SlideMaster

        super().__init__(storage, cache_key)
        self._xml_path = xml_path
        self._slide_master: SlideMaster = slide_master

    @property
    def xml(self) -> ElementTree:
        return self._storage.loader.get_file_xml(self._xml_path)

    def save_xml(self) -> None:
        return self._storage.loader.save_file_xml(self._xml_path, self.xml)

    @cache_persist_property
    def color_rgbs(self) -> Dict[str, str]:
        result: Dict[str, str] = dict()

        for elem in self.xml.xpath('a:themeElements[1]/a:clrScheme[1]/*', namespaces=pptx_xml_ns):
            standard_address_and_tag_name = str(elem.tag)
            tag_name = standard_address_and_tag_name.split('}')[1]
            color = elem[0].get('val')

            if color in SYSTEM_COLOR_NAMES.keys():
                color = SYSTEM_COLOR_NAMES[color]

            result[tag_name] = color

        color_map = self._slide_master.xml.xpath('p:clrMap[1]', namespaces=pptx_xml_ns)[0]
        result['bg1'] = result.get(color_map.attrib['bg1'], '000000')
        result['tx1'] = result.get(color_map.attrib['tx1'], '000000')
        result['bg2'] = result.get(color_map.attrib['bg2'], '000000')
        result['tx2'] = result.get(color_map.attrib['tx2'], '000000')

        return result
