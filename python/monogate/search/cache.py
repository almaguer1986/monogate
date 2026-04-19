"""
monogate.search.cache — LRU-bounded evaluation cache.

Stores tree score results keyed on a canonical hash string so that
identical EML trees are never re-evaluated during a search run.
"""

from __future__ import annotations

from collections import OrderedDict


class EvalCache:
    """LRU-bounded cache mapping tree-hash strings to float scores.

    Args:
        max_size: Maximum number of entries.  When full, the least-recently-
                  used entry is evicted before inserting a new one.
    """

    def __init__(self, max_size: int = 1024) -> None:
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got {max_size}")
        self._max = max_size
        self._store: OrderedDict[str, float] = OrderedDict()

    def get(self, key: str) -> float | None:
        """Return cached score, or None on a cache miss."""
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: str, value: float) -> None:
        """Insert or update an entry, evicting the LRU entry when full."""
        if key in self._store:
            self._store.move_to_end(key)
            self._store[key] = value
            return
        if len(self._store) >= self._max:
            self._store.popitem(last=False)
        self._store[key] = value

    def size(self) -> int:
        """Return the current number of cached entries."""
        return len(self._store)
