import copy
from typing import Any, Dict, List, Optional, Tuple


class CacheKey:
    __slots__ = ('name', 'parent', 'root', 'do_disable_cache', 'postfix')

    def __init__(self, name: str, parent=None, do_disable_cache: bool = None):
        self.name = name
        self.parent: CacheKey = parent
        self.postfix: Optional[str] = None

        if self.parent is None:
            self.root: CacheKey = self
        else:
            self.root: CacheKey = self.parent.root

        if do_disable_cache is not None:
            self.do_disable_cache = do_disable_cache
        else:
            if self.parent is not None:
                self.do_disable_cache = self.parent.do_disable_cache
            else:
                self.do_disable_cache = False

    def __str__(self) -> str:
        reversed_path: List[str] = list()

        if self.postfix is not None:
            reversed_path.append(self.postfix)

        current_key = self
        while current_key is not None:
            reversed_path.append(current_key.name)
            current_key = current_key.parent

        return '/'.join(reversed(reversed_path))

    @property
    def this_or_son_from_postfix(self):
        if self.postfix is None:
            return self
        else:
            return self.make_son(self.postfix)

    def make_son(self, name: str):
        return CacheKey(name, parent=self)


class CachePrefixTreeDict(dict):
    pass


class CachePrefixTree:
    def __init__(self):
        self._tree = CachePrefixTreeDict()

    def __getitem__(self, key: CacheKey) -> Tuple[Any, bool]:
        # reverse linked list using recursion
        def rec(k: CacheKey):
            if k.root == k:
                branch = self._tree  # start
                parent_exists = True
            else:
                branch, parent_exists = rec(k.parent)

            if not parent_exists or branch is None:
                return None, False  # traverse fail

            if k != key:
                inner_branch = branch.get(k.name)  # traverse
                return inner_branch, inner_branch is not None
            else:
                value = branch.get(k.name)  # actual value get
                if value is None:
                    return value, k in branch
                else:
                    return value, True

        return rec(key.this_or_son_from_postfix)

    def __setitem__(self, key: CacheKey, value: Any) -> None:
        def rec(k: CacheKey):
            if k.root == k:
                branch = self._tree
            else:
                branch = rec(k.parent)

            if k != key:
                inner_branch = branch.get(k.name)
                if inner_branch is None:
                    inner_branch = CachePrefixTreeDict()
                    branch[k.name] = inner_branch
                return inner_branch
            else:
                branch[k.name] = value

        rec(key.this_or_son_from_postfix)

    def __delitem__(self, key: CacheKey) -> None:
        def rec(k: CacheKey):
            if k.root == k:
                branch = self._tree
            else:
                branch = rec(k.parent)

            if branch is None:
                return None

            if k != key:
                inner_branch = branch.get(k.name)
                return inner_branch
            else:
                if k.name in branch:
                    del branch[k.name]

        rec(key.this_or_son_from_postfix)

    def __contains__(self, key: CacheKey) -> bool:
        return self[key] is not None

    def get_inner_tree(self) -> Dict[str, Any]:
        return self._tree

    def set_inner_tree(self, tree: Dict[str, Any]) -> None:
        self._tree = tree


class Cacher:
    _PERSISTING_CACHE_ALLOWED_TYPES = (int, float, str)

    def __init__(self):
        self._persisting_cache = CachePrefixTree()
        self._local_cache = CachePrefixTree()
        self._is_persisting_cache_changed_since_load = False

    def cache_persist(self, key: CacheKey, value: Any) -> None:
        if not self._is_ok_for_persisting_cache(value):
            raise ValueError(f'Value of type {type(value)} is not allowed for persisting cache')

        self._persisting_cache[key] = value
        self._is_persisting_cache_changed_since_load = True

    def cache_local(self, key: CacheKey, value: Any) -> None:
        self._local_cache[key] = value

    def delete_from_persisting_cache(self, key: CacheKey) -> None:
        del self._persisting_cache[key]

    def delete_from_local_cache(self, key: CacheKey) -> None:
        del self._local_cache[key]

    def delete_from_any_cache(self, key: CacheKey) -> None:
        self.delete_from_persisting_cache(key)
        self.delete_from_local_cache(key)

    def get_from_persisting_cache(self, key: CacheKey) -> Tuple[Optional[Any], bool]:
        return self._persisting_cache[key]

    def get_from_local_cache(self, key: CacheKey) -> Tuple[Optional[Any], bool]:
        return self._local_cache[key]

    def have_in_persisting_cache(self, key: CacheKey) -> Optional[Any]:
        return key in self._persisting_cache

    def have_in_local_cache(self, key: CacheKey) -> Optional[Any]:
        return key in self._local_cache

    def load_persisting_cache(self, cache: Dict[str, Any]) -> None:
        self._persisting_cache.set_inner_tree(cache)

    def dump_persisting_cache(self) -> Dict[str, Any]:
        return self._persisting_cache.get_inner_tree()

    def duplicate(self):
        new_cacher = Cacher()

        new_cacher._persisting_cache = copy.copy(self._persisting_cache)
        new_cacher._local_cache = copy.deepcopy(self._local_cache)
        new_cacher._is_persisting_cache_changed_since_load = self._is_in_persisting_cache_allowed_types

        return new_cacher

    @property
    def is_persisting_cache_changed_since_load(self) -> bool:
        return self._is_persisting_cache_changed_since_load

    def mark_persisting_cache_saved(self):
        self._is_persisting_cache_changed_since_load = False

    def _is_ok_for_persisting_cache(self, value: Any) -> bool:
        if value is None:
            return True
        if self._is_in_persisting_cache_allowed_types(value):
            return True
        if isinstance(value, list) and \
                all(self._is_in_persisting_cache_allowed_types(it) for it in value):
            return True
        if isinstance(value, dict) and \
                all(isinstance(k, str) for k in value.keys()) and \
                all(self._is_in_persisting_cache_allowed_types(v) for v in value.values()):
            return True
        return False

    def _is_in_persisting_cache_allowed_types(self, value: Any) -> bool:
        return any(isinstance(value, t) for t in self._PERSISTING_CACHE_ALLOWED_TYPES)
