import re
from typing import Optional, List, Iterator

from lxml import etree

from gpptx.pptx_tools.paths import relativize_filepath_relatively_to_root, \
    relativize_filepath_relatively_to_content_dirs, absolutize_filepath_relatively_to_root, \
    absolutize_filepath_relatively_to_content_dirs, SLIDES_PATH_PREFIX, SLIDE_MASTERS_PATH_PREFIX, \
    SLIDE_LAYOUTS_PATH_PREFIX, THEMES_PATH_PREFIX, MEDIA_IMAGES_PATH_PREFIX, ROOT_RELS_PATH_PREFIX
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.pptx.loader import Loader

_REL_INDEX_REGEXP = re.compile('^rId(\d+)$')


def create_blank_rels(loader: Loader, filepath: str) -> None:
    contents = """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>
    """.strip()
    loader.save_file_str(filepath, contents)


def add_mention_in_rels(loader: Loader, rels_filepath: str, new_filepath: str) -> str:
    xml = loader.get_file_xml(rels_filepath)

    last_index = 0
    for rel in xml.xpath('r:Relationship', namespaces=pptx_xml_ns):
        rel_id = rel.get('Id')
        result = _REL_INDEX_REGEXP.match(rel_id)
        index = int(result.group(1))
        last_index = max(last_index, index)

    relation_id = f'rId{last_index+1}'

    is_root_rels = rels_filepath.startswith(ROOT_RELS_PATH_PREFIX)
    if is_root_rels:
        relative_new_filepath = relativize_filepath_relatively_to_root(new_filepath)
    else:
        relative_new_filepath = relativize_filepath_relatively_to_content_dirs(new_filepath)

    item_xml = etree.Element('{%s}Relationship' % pptx_xml_ns['r'])
    item_xml.set('Id', relation_id)
    item_xml.set('Type', detect_relation_type_by_filepath(new_filepath))
    item_xml.set('Target', relative_new_filepath)
    xml.append(item_xml)

    loader.save_file_xml(rels_filepath, xml)

    return relation_id


def delete_mention_in_rels(loader: Loader, rels_filepath: str, relation_id: str) -> None:
    xml = loader.get_file_xml(rels_filepath)

    item_xml = xml.xpath(f'r:Relationship[@Id="{relation_id}"][1]', namespaces=pptx_xml_ns)[0]
    item_xml.getparent().remove(item_xml)

    loader.save_file_xml(rels_filepath, xml)


def find_relation_id_in_rels(loader: Loader, rels_filepath: str, filepath: str) -> Optional[str]:
    xml = loader.get_file_xml(rels_filepath)

    is_root_rels = rels_filepath.startswith(ROOT_RELS_PATH_PREFIX)
    if is_root_rels:
        relative_filepath = relativize_filepath_relatively_to_root(filepath)
    else:
        relative_filepath = relativize_filepath_relatively_to_content_dirs(filepath)

    ids = xml.xpath(f'r:Relationship[@Target="{relative_filepath}"][1]/@Id', namespaces=pptx_xml_ns)
    if len(ids) == 0:
        return None
    return ids[0]


def get_all_relation_paths_in_rels(loader: Loader, rels_filepath: str) -> List[str]:
    return list(_iter_all_relation_paths_in_rels(loader, rels_filepath))


def find_first_relation_path_with_prefix(loader: Loader, rels_filepath: str, prefix: str) -> Optional[str]:
    for path in _iter_all_relation_paths_in_rels(loader, rels_filepath):
        if path.startswith(prefix):
            return path
    return None


def _iter_all_relation_paths_in_rels(loader: Loader, rels_filepath: str) -> Iterator[str]:
    xml = loader.get_file_xml(rels_filepath)

    is_root_rels = rels_filepath.startswith(ROOT_RELS_PATH_PREFIX)

    for relation in xml.xpath(f'r:Relationship', namespaces=pptx_xml_ns):
        relative_filepath = relation.get('Target')
        if is_root_rels:
            abs_filepath = absolutize_filepath_relatively_to_root(relative_filepath)
        else:
            abs_filepath = absolutize_filepath_relatively_to_content_dirs(relative_filepath)
        yield abs_filepath


def detect_relation_type_by_filepath(filepath: str) -> Optional[str]:
    if filepath.startswith(SLIDES_PATH_PREFIX):
        return 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide'
    elif filepath.startswith(SLIDE_MASTERS_PATH_PREFIX):
        return 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster'
    elif filepath.startswith(SLIDE_LAYOUTS_PATH_PREFIX):
        return 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout'
    elif filepath.startswith(THEMES_PATH_PREFIX):
        return 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme'
    elif filepath.startswith(MEDIA_IMAGES_PATH_PREFIX):
        return 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
    else:
        return None
