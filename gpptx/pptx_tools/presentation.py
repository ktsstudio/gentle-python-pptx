from lxml import etree

from gpptx.pptx_tools.paths import PRESENTATION_PATH
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.pptx.loader import Loader


def add_slide_mention_in_presentation(loader: Loader, relation_id: str) -> None:
    xml = loader.get_file_xml(PRESENTATION_PATH)

    last_slide_id = 0
    for it in xml.xpath('p:sldIdLst/p:sldId', namespaces=pptx_xml_ns):
        slide_id = int(it.get('id'))
        last_slide_id = max(last_slide_id, slide_id)
    new_slide_id = last_slide_id + 1

    slide_item_xml = etree.Element('{%s}sldId' % pptx_xml_ns['p'])
    slide_item_xml.set('id', str(new_slide_id))
    slide_item_xml.set('{%s}id' % pptx_xml_ns['r'], relation_id)
    xml.xpath('p:sldIdLst[1]', namespaces=pptx_xml_ns)[0].append(slide_item_xml)

    ext_slide_sections = xml.xpath('p:extLst/p:ext[@uri="{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"][1]',
                                   namespaces=pptx_xml_ns)
    has_slide_sections = len(ext_slide_sections) != 0
    if has_slide_sections:
        ext_slide_sections = ext_slide_sections[0]
        section_slide_item_xml = etree.Element('{%s}sldId' % pptx_xml_ns['p'])
        section_slide_item_xml.set('id', str(new_slide_id))
        t = ext_slide_sections.xpath('p14:sectionLst/p14:section[1]/p14:sldIdLst[1]', namespaces=pptx_xml_ns)[0]
        t.append(section_slide_item_xml)

    loader.save_file_xml(PRESENTATION_PATH, xml)


def delete_slide_mention_in_presentation(loader: Loader, relation_id: str) -> None:
    xml = loader.get_file_xml(PRESENTATION_PATH)

    item_xml = xml.xpath(f'p:sldIdLst/p:sldId[@r:id="{relation_id}"][1]', namespaces=pptx_xml_ns)[0]
    item_xml.getparent().remove(item_xml)

    loader.save_file_xml(PRESENTATION_PATH, xml)


def add_slide_master_mention_in_presentation(loader: Loader, relation_id: str) -> None:
    xml = loader.get_file_xml(PRESENTATION_PATH)

    last_slide_master_id = 0
    for it in xml.xpath('p:sldMasterIdLst/p:sldMasterId', namespaces=pptx_xml_ns):
        slide_master_id = int(it.get('id'))
        last_slide_master_id = max(last_slide_master_id, slide_master_id)
    new_slide_master_id = last_slide_master_id + 1

    slide_item_xml = etree.Element('{%s}sldMasterId' % pptx_xml_ns['p'])
    slide_item_xml.set('id', str(new_slide_master_id))
    slide_item_xml.set('{%s}id' % pptx_xml_ns['r'], relation_id)
    xml.xpath('p:sldMasterIdLst[1]', namespaces=pptx_xml_ns)[0].append(slide_item_xml)

    loader.save_file_xml(PRESENTATION_PATH, xml)
