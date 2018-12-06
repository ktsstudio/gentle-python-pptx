import re
from typing import Set, Optional, Iterable

from lxml import etree

from gpptx.pptx_tools.paths import find_last_index_of_content, absolutize_filepath_relatively_to_content_dirs, \
    make_rels_path
from gpptx.pptx_tools.rels import create_blank_rels
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.pptx.loader import Loader

_PATH_DIR_CONTENT_NAME_EXT_REGEX = re.compile('^\.\./(.+?)/(.+?)\d+\.(.+)$')


class _CopyRelationState:
    def __init__(self):
        self._copied_files = dict()
        self._srcs = set()
        self._dests = set()

    def track(self, src_filepath: str, dest_filepath: str) -> None:
        self._copied_files[src_filepath] = dest_filepath
        self._srcs.add(src_filepath)
        self._dests.add(dest_filepath)

    def has_src(self, filepath: str) -> bool:
        return filepath in self._srcs

    def has_dest(self, filepath: str) -> bool:
        return filepath in self._dests

    def src_to_dest(self, filepath) -> str:
        return self._copied_files[filepath]

    @property
    def dest_filepaths(self) -> Set[str]:
        return self._dests


def copy_relations_recursively(src_loader: Loader, src_rels_filepath: str,
                               dest_loader: Loader, dest_rels_filepath: str,
                               state: Optional[_CopyRelationState] = None) -> Iterable[str]:
    """
    :return: abs destination paths of what was copied
    """

    if state is None:
        state = _CopyRelationState()

    src_xml = src_loader.get_file_xml(src_rels_filepath)
    dest_xml = dest_loader.get_file_xml(dest_rels_filepath)

    target_filepaths_queue = list()
    repeated_target_filepaths_queue = list()

    for src_rel in src_xml.xpath('r:Relationship', namespaces=pptx_xml_ns):
        # make dest target filepath
        relative_src_target = src_rel.get('Target')

        match_result = _PATH_DIR_CONTENT_NAME_EXT_REGEX.match(relative_src_target)
        dir_name = match_result.group(1)
        content_name = match_result.group(2)
        ext = match_result.group(3)

        last_target_index = find_last_index_of_content(loader=dest_loader, content_name=content_name, dir_name=dir_name)
        dest_target_index = last_target_index + 1

        relative_dest_target = f'../{dir_name}/{content_name}{dest_target_index}.{ext}'

        # copy file
        abs_src_target = absolutize_filepath_relatively_to_content_dirs(relative_src_target)
        abs_dest_target = absolutize_filepath_relatively_to_content_dirs(relative_dest_target)

        contents = src_loader.get_file(abs_src_target)
        dest_loader.save_file(abs_dest_target, contents)

        # add this file's rels to copy queue
        src_rel_filepath = make_rels_path(abs_src_target)
        dest_rel_filepath = make_rels_path(abs_dest_target)

        if src_loader.does_file_exist(src_rel_filepath):
            if state.has_src(abs_src_target):
                repeated_target_filepaths_queue.append((src_rel_filepath, dest_rel_filepath))
            else:
                target_filepaths_queue.append((src_rel_filepath, dest_rel_filepath))

        # track
        state.track(abs_src_target, abs_dest_target)

        # track in rels
        dest_item_xml = etree.Element('{%s}Relationship' % pptx_xml_ns['r'])
        dest_item_xml.set('Id', src_rel.get('Id'))
        dest_item_xml.set('Type', src_rel.get('Type'))
        dest_item_xml.set('Target', relative_dest_target)
        dest_xml.append(dest_item_xml)

    dest_loader.save_file_xml(dest_rels_filepath, dest_xml)

    for src_rel_filepath, dest_rel_filepath in target_filepaths_queue:
        create_blank_rels(loader=dest_loader,
                          filepath=dest_rel_filepath)
        copy_relations_recursively(src_loader=src_loader, src_rels_filepath=src_rel_filepath,
                                   dest_loader=dest_loader, dest_rels_filepath=dest_rel_filepath,
                                   state=state)

    for src_rel_filepath, dest_rel_filepath in repeated_target_filepaths_queue:
        create_blank_rels(loader=dest_loader,
                          filepath=dest_rel_filepath)
        _copy_relations_recursively_repeated_case(src_loader=src_loader, src_rels_filepath=src_rel_filepath,
                                                  dest_loader=dest_loader, dest_rels_filepath=dest_rel_filepath,
                                                  state=state)

    return state.dest_filepaths


def _copy_relations_recursively_repeated_case(src_loader: Loader, src_rels_filepath: str,
                                              dest_loader: Loader, dest_rels_filepath: str,
                                              state: _CopyRelationState) -> None:
    src_xml = src_loader.get_file_xml(src_rels_filepath)
    dest_xml = dest_loader.get_file_xml(dest_rels_filepath)

    for src_rel in src_xml.xpath('r:Relationship', namespaces=pptx_xml_ns):
        # make dest target filepath
        relative_src_target = src_rel.get('Target')
        abs_src_target = absolutize_filepath_relatively_to_content_dirs(relative_src_target)

        # track in rels
        dest_item_xml = etree.Element('{%s}Relationship' % pptx_xml_ns['r'])
        dest_item_xml.set('Id', src_rel.get('Id'))
        dest_item_xml.set('Type', src_rel.get('Type'))
        dest_item_xml.set('Target', state.src_to_dest(abs_src_target))
        dest_xml.append(dest_item_xml)

    dest_loader.save_file_xml(dest_rels_filepath, dest_xml)
