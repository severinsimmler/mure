from asyncio import Lock


class Consumption:
    """Tracks the consumption."""

    def __init__(self, num_consumables: int):
        self.consumables = set(range(num_consumables))
        self.scheduled = set()
        self._lock = Lock()

    @property
    def is_done(self) -> bool:
        """Check if all items have been consumed and none are scheduled.

        Returns
        -------
        bool
            True if all items have been consumed and none are scheduled, False otherwise.
        """
        return len(self.consumables) == 0 and len(self.scheduled) == 0

    async def anext_priority(self) -> int | None:
        """Get the next priority to consume.

        Returns
        -------
        int | None
            The next priority to consume, or None if all have been consumed.
        """
        async with self._lock:
            unscheduled = self.consumables - self.scheduled

            if not unscheduled:
                return None

            priority = min(unscheduled)

            self.scheduled.add(priority)

            return priority

    async def aconsume(self, priority: int):
        """Consume the given priority.

        Parameters
        ----------
        priority : int
            Priority of the consumed item.
        """
        async with self._lock:
            self.scheduled.remove(priority)
            self.consumables.remove(priority)
