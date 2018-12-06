import copy
from io import BytesIO
from typing import Dict, Set, BinaryIO, Union, Iterable
from zipfile import ZipFile

from lxml import etree
from lxml.etree import ElementTree


class Loader:
    def __init__(self):
        self._zip: ZipFile = None

        self._all_files: Set[str] = None
        self._deleted_files: Set[str] = set()

        self._xml_cache: Dict[str, ElementTree] = dict()
        self._changed_files_cache: Dict[str, bytes] = dict()
        self._changed_xml_cache: Dict[str, ElementTree] = dict()

    def load(self, src: Union[BinaryIO, BytesIO]) -> None:
        self._zip = ZipFile(src, mode='r')
        self._all_files = set(self._zip.namelist())

    def save(self, dest: Union[BinaryIO, BytesIO]) -> None:
        with ZipFile(dest, mode='w') as new_zip:
            processed_files = set()

            processed_files.update(self._deleted_files)  # skip deleted files

            for path, tree in self._changed_xml_cache.items():
                if path in processed_files:
                    continue
                new_zip.writestr(path, self._stringify_xml(tree))
                processed_files.add(path)

            for path, blob in self._changed_files_cache.items():
                if path in processed_files:
                    continue
                new_zip.writestr(path, blob)
                processed_files.add(path)

            for path in self._all_files:
                if path in processed_files:
                    continue
                new_zip.writestr(path, self._zip.read(path))

    def duplicate(self):
        new_loader = Loader()

        new_loader._zip = self._zip

        new_loader._all_files = self._all_files
        new_loader._deleted_files = copy.deepcopy(self._deleted_files)

        new_loader._xml_cache = self._xml_cache
        new_loader._changed_files_cache = copy.deepcopy(self._changed_files_cache)
        new_loader._changed_xml_cache = copy.deepcopy(self._changed_xml_cache)

        return new_loader

    def get_filelist(self) -> Iterable[str]:
        return self._all_files - self._deleted_files

    def does_file_exist(self, filepath: str) -> bool:
        return filepath not in self._deleted_files and filepath in self._all_files

    def get_file(self, filepath: str) -> bytes:
        if filepath in self._changed_files_cache:
            return self._changed_files_cache[filepath]

        if filepath in self._changed_xml_cache:
            return self._stringify_xml(filepath)

        return self._zip.read(filepath)

    def get_file_str(self, filepath: str) -> str:
        return self.get_file(filepath).decode('utf-8')

    def get_file_xml(self, filepath: str) -> ElementTree:
        if filepath in self._changed_xml_cache:
            return self._changed_xml_cache[filepath]

        if filepath in self._xml_cache:
            return self._xml_cache[filepath]

        blob = self.get_file(filepath)
        tree = self._parse_xml(blob)
        self._xml_cache[filepath] = tree
        return tree

    def save_file(self, filepath: str, contents: bytes) -> None:
        self._clear_file_caches(filepath)
        self._changed_files_cache[filepath] = contents

    def save_file_str(self, filepath: str, contents: str) -> None:
        self.save_file(filepath, contents.encode('utf-8'))

    def save_file_xml(self, filepath: str, tree: ElementTree) -> None:
        self._clear_file_caches(filepath)
        self._changed_xml_cache[filepath] = tree

    def copy_file(self, old_filepath: str, new_filepath: str) -> None:
        self._clear_file_caches(new_filepath)
        self._changed_files_cache[new_filepath] = self.get_file(old_filepath)

    def copy_file_from(self, loader, filepath: str, new_filepath: str) -> None:
        self._clear_file_caches(new_filepath)
        self._changed_files_cache[new_filepath] = loader.get_file(filepath)

    def delete_file(self, filepath: str) -> None:
        self._clear_file_caches(filepath)
        self._deleted_files.add(filepath)

    def _clear_file_caches(self, filepath: str) -> None:
        self._xml_cache.pop(filepath, default=None)
        self._changed_files_cache.pop(filepath, default=None)
        self._changed_xml_cache.pop(filepath, default=None)

    @staticmethod
    def _parse_xml(blob: bytes) -> ElementTree:
        blob = blob.decode('utf-8')
        blob = blob.lstrip()
        blob = blob.encode('utf-8')
        return etree.fromstring(blob)

    @staticmethod
    def _stringify_xml(tree: ElementTree) -> bytes:
        return etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
