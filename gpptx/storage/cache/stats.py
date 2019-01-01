class Stats:
    def __init__(self):
        self._persisting_cache_hits = 0
        self._persisting_cache_misses = 0
        self._local_cache_hits = 0
        self._local_cache_misses = 0

    @property
    def persisting_cache_hits(self) -> int:
        return self._persisting_cache_hits

    @property
    def persisting_cache_misses(self) -> int:
        return self._persisting_cache_misses

    @property
    def local_cache_hits(self) -> int:
        return self._local_cache_hits

    @property
    def local_cache_misses(self) -> int:
        return self._local_cache_misses

    def track_persisting_cache_hit(self) -> None:
        self._persisting_cache_hits += 1

    def track_persisting_cache_miss(self) -> None:
        self._persisting_cache_misses += 1

    def track_local_cache_hit(self) -> None:
        self._local_cache_hits += 1

    def track_local_cache_miss(self) -> None:
        self._local_cache_misses += 1
