from abc import ABC
from functools import update_wrapper, WRAPPER_ASSIGNMENTS
from typing import Callable, List, Any, Dict, Tuple

from gpptx.storage.storage import PresentationStorage


class CacheDecoratable(ABC):
    __slots__ = ('_storage', '_storage_cache_key')


def cache_persist(f: Callable) -> Callable:
    return _CacheDecorator(f, use_persisting_cache=True)


def cache_local(f: Callable) -> Callable:
    return _CacheDecorator(f, use_persisting_cache=False)


class _CacheDecorator:
    def __init__(self, fn: Callable, use_persisting_cache: bool):
        self._fn = fn
        self._use_persisting_cache = use_persisting_cache
        update_wrapper(self, self._fn, assigned=WRAPPER_ASSIGNMENTS, updated=[])

    # noinspection PyProtectedMember
    def __call__(self, fn_self: CacheDecoratable, *args, **kwargs):
        if not fn_self._storage_cache_key.do_disable_cache:
            call_cache_key_name = self._make_call_cache_key_name(self._fn.__name__, args, kwargs)
            son_cache_key = fn_self._storage_cache_key.make_son(call_cache_key_name)
        else:
            son_cache_key = None

        if not fn_self._storage_cache_key.do_disable_cache:
            value = self._get_cache_get_fn(fn_self._storage)(son_cache_key)
            if value is not None:
                return value

        value = self._fn(fn_self, *args, **kwargs)
        if not fn_self._storage_cache_key.do_disable_cache:
            self._get_cache_save_fn(fn_self._storage)(son_cache_key, value)
        return value

    def __getattr__(self, k: str) -> Any:
        if k[0] == '_':
            v = self.__dict__.get(k)
            if v is not None:
                return v
        return getattr(self._fn, k)

    def __setattr__(self, k: str, v: Any) -> None:
        if k[0] == '_':
            self.__dict__[k] = v
            return
        setattr(self._fn, k, v)

    # noinspection PyProtectedMember,PyUnresolvedReferences
    def clear_cache(self) -> None:
        fn_self: CacheDecoratable = self.__self__
        call_cache_key_name = self._make_call_cache_key_name(self._fn.__name__)
        son_cache_key = fn_self._storage_cache_key.make_son(call_cache_key_name)
        fn_self._storage.cacher.delete_from_any_cache(son_cache_key)

    def _get_cache_get_fn(self, storage: PresentationStorage) -> Callable:
        if self._use_persisting_cache:
            return storage.cacher.get_from_persisting_cache
        else:
            return storage.cacher.get_from_local_cache

    def _get_cache_save_fn(self, storage: PresentationStorage) -> Callable:
        if self._use_persisting_cache:
            return storage.cacher.cache_persist
        else:
            return storage.cacher.cache_local

    @staticmethod
    def _make_call_cache_key_name(func_name: str, args: Tuple[Any] = None, kwargs: Dict[str, Any] = None) -> str:
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
