from asyncio import Event, PriorityQueue

from mure.consumption import Consumption
from mure.models import Response


class Queue:
    """Queue to hold responses."""

    def __init__(self, total_size: int):
        self.total_size = total_size
        self._consumption = Consumption(self.total_size)
        self._queue = PriorityQueue()
        self._events = [Event() for _ in range(self.total_size)]

    async def put(self, priority: int, response: Response):
        """Add an item to the queue.

        Parameters
        ----------
        priority : int
            Priority of the request.
        response : Response
            The response to add to the queue.
        """
        await self._queue.put((priority, response))

        # signal that the response is ready
        self._events[priority].set()

    async def get(self, priority: int) -> Response | None:
        """Get the next item from the queue.

        Returns
        -------
        Response | None
            The next item from the queue.
        """
        if self._consumption.is_done:
            return None

        # wait for the response to be ready...
        await self._events[priority].wait()

        # ...now actually get it...
        _priority, response = await self._queue.get()

        if priority != _priority:
            raise ValueError("Inconsistency between priority and fetched item")

        # ...and track the consumption
        await self._consumption.aconsume(priority)

        return response

    async def get_next(self) -> Response | None:
        """Get the next item from the queue based on priority.

        Returns
        -------
        Response | None
            The next item from the queue.
        """
        if self._consumption.is_done:
            return None

        priority = await self._consumption.anext_priority()

        if priority is None:
            return None

        return await self.get(priority)

    def empty(self) -> bool:
        """Whether the queue is empty."""
        return self._queue.empty()
