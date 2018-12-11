from abc import ABC
from functools import update_wrapper, WRAPPER_ASSIGNMENTS
from typing import Callable, List, Any, Dict, Collection, Type

from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.storage import PresentationStorage


class CacheDecoratable(ABC):
    __slots__ = ('_storage', '_storage_cache_key')


def cache_persist(f: Callable) -> Callable:
    return _CacheDecoratorMethod(f, do_use_persisting_cache=True)


def cache_local(f: Callable) -> Callable:
    return _CacheDecoratorMethod(f, do_use_persisting_cache=False)


def cache_persist_property(f: Callable):
    return _CacheDecoratorProperty(f, do_use_persisting_cache=True)


def cache_local_property(f: Callable):
    return _CacheDecoratorProperty(f, do_use_persisting_cache=False)


def clear_decorator_cache(obj: CacheDecoratable, func_name: str,
                          args: Collection[Any] = None, kwargs: Dict[str, Any] = None):
    call_cache_key_name = _make_call_cache_key_name(func_name, args, kwargs)
    # noinspection PyProtectedMember
    son_cache_key = obj._storage_cache_key.make_son(call_cache_key_name)
    # noinspection PyProtectedMember
    obj._storage.cacher.delete_from_any_cache(son_cache_key)


class _BaseCacheDecorator(ABC):
    def __init__(self, do_use_persisting_cache: bool):
        self._do_use_persisting_cache = do_use_persisting_cache
        self._serializer_fn: Callable[[Any], Any] = None
        self._unserializer_fn: Callable[[Any], Any] = None

    def _call(self, fn: Callable, fn_name: str,
              fn_self: CacheDecoratable, args: Collection[Any] = None, kwargs: Dict[str, Any] = None,
              do_note_args_in_cache: bool = True):
        # noinspection PyProtectedMember
        if not fn_self._storage_cache_key.do_disable_cache:
            # noinspection PyProtectedMember
            call_cache_key = self._make_call_cache_key(fn_self._storage_cache_key, fn_name, args, kwargs,
                                                       do_note_args_in_cache=do_note_args_in_cache)
        else:
            call_cache_key = None

        # noinspection PyProtectedMember
        if not fn_self._storage_cache_key.do_disable_cache:
            # noinspection PyProtectedMember
            value = self._get_from_cache(call_cache_key, fn_self)
            if value is not None:
                return value

        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()
        value = fn(fn_self, *args, **kwargs)

        # noinspection PyProtectedMember
        if not fn_self._storage_cache_key.do_disable_cache:
            # noinspection PyProtectedMember
            self._save_to_cache(call_cache_key, value, fn_self)
        return value

    @staticmethod
    def _make_call_cache_key(storage_cache_key: CacheKey,
                             fn_name: str, args: Collection[Any], kwargs: Dict[str, Any],
                             do_note_args_in_cache: bool):
        if do_note_args_in_cache:
            call_cache_key_name = _make_call_cache_key_name(fn_name, args, kwargs)
        else:
            call_cache_key_name = _make_call_cache_key_name(fn_name)
        return storage_cache_key.make_son(call_cache_key_name)

    def _get_from_cache(self, call_cache_key: CacheKey, fn_self: CacheDecoratable):
        # noinspection PyProtectedMember
        get_fn = self._get_cache_get_fn(fn_self._storage)
        value = get_fn(call_cache_key)
        if self._unserializer_fn is not None and value is not None:
            value = self._unserializer_fn(fn_self, value)
        return value

    def _save_to_cache(self, call_cache_key: CacheKey, value: Any, fn_self: CacheDecoratable):
        # noinspection PyProtectedMember
        save_fn = self._get_cache_save_fn(fn_self._storage)
        if self._serializer_fn is not None and value is not None:
            value = self._serializer_fn(fn_self, value)
        save_fn(call_cache_key, value)

    def _get_cache_get_fn(self, storage: PresentationStorage) -> Callable:
        if self._do_use_persisting_cache:
            return storage.cacher.get_from_persisting_cache
        else:
            return storage.cacher.get_from_local_cache

    def _get_cache_save_fn(self, storage: PresentationStorage) -> Callable:
        if self._do_use_persisting_cache:
            return storage.cacher.cache_persist
        else:
            return storage.cacher.cache_local


class _CacheDecoratorMethod(_BaseCacheDecorator):
    _DECORATOR_MEMBERS = ('_do_use_persisting_cache', '_serializer_fn', '_unserializer_fn', '_fn')

    def __init__(self, fn: Callable, do_use_persisting_cache: bool):
        super().__init__(do_use_persisting_cache)
        self._fn = fn
        update_wrapper(self, self._fn, assigned=WRAPPER_ASSIGNMENTS, updated=())

    def __get__(self, fn_self: CacheDecoratable, fn_cls: Type) -> Callable:
        return lambda *args, **kwargs: self._call(self._fn, self._fn.__name__, fn_self, args, kwargs)

    def __call__(self, fn_self: CacheDecoratable, *args, **kwargs) -> Any:
        return self._call(self._fn, self._fn.__name__, fn_self, args, kwargs)

    def __getattr__(self, k: str) -> Any:
        if k in self._DECORATOR_MEMBERS:
            return self.__dict__[k]
        return getattr(self._fn, k)

    def __setattr__(self, k: str, v: Any) -> None:
        if k in self._DECORATOR_MEMBERS:
            self.__dict__[k] = v
            return
        setattr(self._fn, k, v)

    def cache_serializer(self, serializer_fn: Callable[[Any], Any]):
        self._serializer_fn = serializer_fn
        return self

    def cache_unserializer(self, unserializer_fn: Callable[[Any], Any]):
        self._unserializer_fn = unserializer_fn
        return self


class _CacheDecoratorProperty(_BaseCacheDecorator):
    _DECORATOR_MEMBERS = ('_do_use_persisting_cache', '_serializer_fn', '_unserializer_fn', '_getter_fn', '_setter_fn')

    def __init__(self, getter_fn: Callable[[], Any], do_use_persisting_cache: bool):
        super().__init__(do_use_persisting_cache)
        self._getter_fn = getter_fn
        self._setter_fn: Callable[[Any], None] = None

    def __get__(self, fn_self: CacheDecoratable, fn_cls: Type) -> Any:
        return self._call(self._getter_fn, self._getter_fn.__name__, fn_self, do_note_args_in_cache=False)

    def __set__(self, fn_self: CacheDecoratable, value: Any) -> None:
        if self._setter_fn is None:
            raise AttributeError
        self._setter_fn(fn_self, value)
        clear_decorator_cache(fn_self, self._getter_fn.__name__)

    def __getattr__(self, k: str) -> Any:
        if k in self._DECORATOR_MEMBERS:
            return self.__dict__[k]
        return getattr(self._getter_fn, k)

    def __setattr__(self, k: str, v: Any) -> None:
        if k in self._DECORATOR_MEMBERS:
            self.__dict__[k] = v
            return
        setattr(self._getter_fn, k, v)

    def setter(self, setter_fn: Callable[[Any], None]):
        self._setter_fn = setter_fn
        return self

    def cache_serializer(self, serializer_fn: Callable[[Any], Any]):
        self._serializer_fn = serializer_fn
        return self

    def cache_unserializer(self, unserializer_fn: Callable[[Any], Any]):
        self._unserializer_fn = unserializer_fn
        return self


def _make_call_cache_key_name(func_name: str, args: Collection[Any] = None, kwargs: Dict[str, Any] = None) -> str:
    parts: List[str] = list()
    parts.append(func_name)
    if args is not None and len(args) != 0:
        for i, it in enumerate(args):
            parts.append(str(i))
            parts.append(str(it))
    if kwargs is not None and len(kwargs) != 0:
        for k, v in kwargs.items():
            parts.append(str(k))
            parts.append(str(v))
    return '.'.join(parts)

