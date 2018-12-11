from abc import ABC
from typing import Callable, List

from lxml.etree import ElementTree


class LazyElementTree(ABC):
    __slots__ = ()

    def __call__(self):
        raise NotImplementedError


class LazyElementTreeByFunction(LazyElementTree):
    __slots__ = ('_fn',)

    def __init__(self, fn: Callable[[], ElementTree]):
        # fn must be decorated with @cache_local
        self._fn = fn

    def __call__(self):
        return self._fn()


class LazyElementTreeList:
    __slots__ = ('_create_fn', '_length', '_invalidate_length_fn', '_ghost_children_indexes_sorted')

    def __init__(self, create_fn: Callable[[], List[ElementTree]], length: int, invalidate_length_fn: Callable[[], None]):
        # create_fn must be decorated with @cache_local
        self._create_fn = create_fn
        self._length = length
        self._invalidate_length_fn = invalidate_length_fn
        self._ghost_children_indexes_sorted: List[int] = list()

    def __getitem__(self, index: int) -> LazyElementTree:
        shift = 0
        for it in self._ghost_children_indexes_sorted:
            if it > index:
                break
            shift += 1

        return LazyElementTreeByListItem(self, index+shift)

    def __iter__(self):
        shift = 0
        ghost_children_indexes_cursor = 0

        for i in range(self._length):
            if ghost_children_indexes_cursor < len(self._ghost_children_indexes_sorted):
                if self._ghost_children_indexes_sorted[ghost_children_indexes_cursor] == i:
                    shift += 1
                    ghost_children_indexes_cursor += 1

            yield LazyElementTreeByListItem(self, i+shift)

    def __len__(self) -> int:
        return self._length

    def append(self, item: ElementTree, do_invalidate_len_cache: bool = True) -> None:
        self._create_fn().append(item)
        self._length += 1
        if do_invalidate_len_cache:
            self._invalidate_length_fn()

    def pop(self, index: int,
            do_affect_xml: bool = True, was_xml_affected_already: bool = False,
            do_invalidate_len_cache: bool = True) -> None:
        if not was_xml_affected_already:
            if do_affect_xml:
                self._create_fn().pop(index)

        self._length -= 1

        if not do_affect_xml:
            self._ghost_children_indexes_sorted.append(index)
            self._ghost_children_indexes_sorted.sort()

        if do_invalidate_len_cache:
            self._invalidate_length_fn()

    def _get(self, index: int) -> ElementTree:
        return self._create_fn()[index]


class LazyElementTreeByListItem(LazyElementTree):
    __slots__ = ('_lazy_list', '_index')

    def __init__(self, lazy_list, index: int):
        self._lazy_list: LazyElementTreeList = lazy_list
        self._index = index

    def __call__(self):
        # noinspection PyProtectedMember
        return self._lazy_list._get(self._index)

