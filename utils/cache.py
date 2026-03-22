"""Bounded TTL cache to avoid unbounded memory growth."""

import time
from collections import OrderedDict
from typing import Any


class BoundedTTLCache:
    """LRU-style eviction when max_size is exceeded; entries expire after ttl seconds."""

    def __init__(self, max_size: int = 64, ttl_seconds: float = 300.0) -> None:
        self._max_size = max(1, max_size)
        self._ttl = ttl_seconds
        self._data: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._data:
            return None
        entry = self._data[key]
        if time.time() - entry["timestamp"] > self._ttl:
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return entry["data"]

    def set(self, key: str, value: Any) -> None:
        if key in self._data:
            del self._data[key]
        self._data[key] = {"timestamp": time.time(), "data": value}
        self._data.move_to_end(key)
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()
