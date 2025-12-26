import asyncio


class MessageTracker:
    """Track message order to decide whether later messages inserted during wait."""

    def __init__(self) -> None:
        self._counter = 0
        self._lock = asyncio.Lock()

    async def mark_new(self) -> int:
        """Increment counter and return the value for this message."""
        async with self._lock:
            self._counter += 1
            return self._counter

    async def diff_since(self, previous: int) -> int:
        """Return how many messages have appeared since `previous`."""
        async with self._lock:
            return self._counter - previous
