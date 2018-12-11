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
    __slots__ = ('_create_fn', '_length', '_invalidate_length_fn')

    def __init__(self, create_fn: Callable[[], List[ElementTree]], length: int, invalidate_length_fn: Callable[[], None]):
        # create_fn must be decorated with @cache_local
        self._create_fn = create_fn
        self._length = length
        self._invalidate_length_fn = invalidate_length_fn

    def __getitem__(self, index: int) -> LazyElementTree:
        return LazyElementTreeByListItem(self, index)

    def __iter__(self):
        for i in range(self._length):
            yield LazyElementTreeByListItem(self, i)

    def __len__(self) -> int:
        return self._length

    def append(self, item: ElementTree) -> None:
        self._create_fn().append(item)
        self._length += 1
        self._invalidate_length_fn()

    def pop(self, index: int) -> None:
        self._create_fn().pop(index)
        self._length -= 1
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

