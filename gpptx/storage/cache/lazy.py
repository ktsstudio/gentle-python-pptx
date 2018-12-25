from abc import ABC
from typing import Callable, List, Any, Set, Optional, Iterator, Tuple


class Lazy(ABC):
    __slots__ = ()

    def __call__(self) -> Any:
        raise NotImplementedError


class LazyByFunction(Lazy):
    __slots__ = ('_fn', '_value', '_notify_new_value_fn')

    def __init__(self, fn: Callable[[], Any]):
        self._fn = fn
        self._value = None
        self._notify_new_value_fn = None

    def __call__(self) -> Any:
        self._ensure_value()
        return self._value

    def supply_and_bind_cache(self, value: Optional[Any], notify_new_value_fn: Callable[[], Any]):
        if value is not None:
            self._value = value
        self._notify_new_value_fn = notify_new_value_fn

    def _ensure_value(self):
        if self._value is None:
            self._value = self._fn()
            self._notify_new_value()

    def _notify_new_value(self):
        if self._notify_new_value_fn is not None:
            self._notify_new_value_fn(self._value)


class LazyList:
    __slots__ = ('_create_fn', '_buffer', '_length', '_deleted_indexes',
                 '_notify_new_buffer_fn', '_notify_new_length_fn', '_notify_new_deleted_indexes_fn')

    def __init__(self, create_fn: Callable[[], List[Any]]):
        self._create_fn = create_fn
        self._buffer: Optional[List[Any]] = None
        self._length: Optional[int] = None
        self._deleted_indexes: Set[int] = set()
        self._notify_new_buffer_fn: Optional[Callable[[List[Any]], None]] = None
        self._notify_new_length_fn: Optional[Callable[[int], None]] = None
        self._notify_new_deleted_indexes_fn: Optional[Callable[[Set[int]], None]] = None

    def __iter__(self) -> Iterator[Lazy]:
        for i in self.iter_indexes():
            yield LazyByListItem(self, i)

    def __len__(self) -> int:
        self._ensure_length()
        return self._length - len(self._deleted_indexes)

    def __getitem__(self, index: int) -> Lazy:
        assert index not in self._deleted_indexes
        return LazyByListItem(self, index)

    def supply_and_bind_cache(self,
                              buffer: Optional[List[Any]], length: Optional[int], deleted_indexes: Optional[Set[int]],
                              notify_new_buffer_fn: Callable[[List[Any]], None],
                              notify_new_length_fn: Callable[[int], None],
                              notify_new_deleted_indexes_fn: Callable[[Set[int]], None]) -> None:
        if buffer is not None:
            self._buffer = buffer
        if length is not None:
            self._length = length
        if deleted_indexes is not None:
            self._deleted_indexes = deleted_indexes

        if self._buffer is not None and self._length is not None:
            assert len(self._buffer) == self._length

        self._notify_new_buffer_fn = notify_new_buffer_fn
        self._notify_new_length_fn = notify_new_length_fn
        self._notify_new_deleted_indexes_fn = notify_new_deleted_indexes_fn

    def iter_indexes(self) -> Iterator[int]:
        self._ensure_length()
        for i in range(self._length):
            if i in self._deleted_indexes:
                continue
            yield i

    def iter_enumerate(self) -> Iterator[Tuple[int, Any]]:
        for i in self.iter_indexes():
            yield i, LazyByListItem(self, i)

    def append(self, item: Any) -> None:
        self._ensure_buffer()
        self._ensure_length()
        self._buffer.append(item)
        self._length += 1
        self._notify_new_buffer()
        self._notify_new_length()

    def pop(self, index: int) -> None:
        self._deleted_indexes.add(index)
        self._notify_new_deleted_indexes()

    @property
    def len_with_holes(self):
        self._ensure_length()
        return self._length

    def _get(self, index: int) -> Any:
        self._ensure_buffer()
        return self._buffer[index]

    def _ensure_buffer(self):
        if self._buffer is None:
            self._buffer = self._create_fn()
            if len(self._deleted_indexes) != 0:
                self._recreate_holes()
                if self._length is not None:
                    assert len(self._buffer) == self._length
            self._notify_new_buffer()

    def _recreate_holes(self):
        for i in sorted(self._deleted_indexes):
            self._buffer.insert(i, None)

    def _ensure_length(self):
        if self._length is None:
            self._ensure_buffer()
            self._length = len(self._buffer)

    def _notify_new_buffer(self):
        if self._notify_new_buffer_fn:
            self._notify_new_buffer_fn(self._buffer)

    def _notify_new_length(self):
        if self._notify_new_length_fn:
            self._notify_new_length_fn(self._length)

    def _notify_new_deleted_indexes(self):
        if self._notify_new_deleted_indexes_fn:
            self._notify_new_deleted_indexes_fn(self._deleted_indexes)


class LazyByListItem(Lazy):
    __slots__ = ('_lazy_list', '_index')

    def __init__(self, lazy_list: LazyList, index: int):
        self._lazy_list = lazy_list
        self._index = index

    def __call__(self) -> Any:
        # noinspection PyProtectedMember
        return self._lazy_list._get(self._index)

