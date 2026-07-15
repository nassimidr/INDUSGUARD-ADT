"""Cache LRU/TTL des messages déjà traités."""

from collections import OrderedDict
import time
from typing import Any


class IdempotencyCache:
    def __init__(self, maximum_size: int = 5000, ttl_seconds: float = 3600) -> None:
        self.maximum_size = int(maximum_size); self.ttl_seconds = float(ttl_seconds)
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, message_id: str) -> Any | None:
        self.cleanup(); item = self._items.get(message_id)
        if not item: return None
        self._items.move_to_end(message_id); return item[1]

    def contains(self, message_id: str) -> bool:
        self.cleanup(); return message_id in self._items

    def put(self, message_id: str, response: Any = True) -> None:
        self._items[message_id] = (time.monotonic(), response); self._items.move_to_end(message_id)
        while len(self._items) > self.maximum_size: self._items.popitem(last=False)

    def cleanup(self) -> None:
        cutoff = time.monotonic() - self.ttl_seconds
        for key in list(self._items):
            if self._items[key][0] >= cutoff: break
            self._items.pop(key, None)

    def __len__(self) -> int:
        self.cleanup(); return len(self._items)
