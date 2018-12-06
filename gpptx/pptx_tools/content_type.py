from typing import Optional

from lxml import etree

from gpptx.pptx_tools.paths import CONTENT_TYPES_PATH, SLIDES_PATH_PREFIX, SLIDE_MASTERS_PATH_PREFIX, \
    SLIDE_LAYOUTS_PATH_PREFIX, THEMES_PATH_PREFIX
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.pptx.loader import Loader


def add_mention_in_content_type(loader: Loader, filepath: str) -> None:
    content_type = detect_content_type_by_filepath(filepath)
    if content_type is None:
        return

    xml = loader.get_file_xml(CONTENT_TYPES_PATH)

    filepath_with_slash = f'/{filepath}'
    item_xml = etree.Element('{%s}Override' % pptx_xml_ns['c'])
    item_xml.set('PartName', filepath_with_slash)
    item_xml.set('ContentType', content_type)
    xml.append(item_xml)

    loader.save_file_xml(CONTENT_TYPES_PATH, xml)


def delete_mention_in_content_type(loader: Loader, filepath: str) -> None:
    xml = loader.get_file_xml(CONTENT_TYPES_PATH)

    filepath_with_slash = f'/{filepath}'
    item_xml = xml.xpath(f'c:Override[@PartName="{filepath_with_slash}"][1]', namespaces=pptx_xml_ns)[0]
    item_xml.getparent().remove(item_xml)

    loader.save_file_xml(CONTENT_TYPES_PATH, xml)


def detect_content_type_by_filepath(filepath: str) -> Optional[str]:
    if filepath.startswith(SLIDES_PATH_PREFIX):
        return 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'
    elif filepath.startswith(SLIDE_MASTERS_PATH_PREFIX):
        return 'application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'
    elif filepath.startswith(SLIDE_LAYOUTS_PATH_PREFIX):
        return 'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'
    elif filepath.startswith(THEMES_PATH_PREFIX):
        return 'application/vnd.openxmlformats-officedocument.theme+xml'
    else:
        return None
