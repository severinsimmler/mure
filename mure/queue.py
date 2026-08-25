from asyncio import Event

from mure.models import Response


class Queue:
    """Queue to hold responses until they are consumed in order."""

    def __init__(self, total_size: int):
        self.total_size = total_size
        self._responses: dict[int, Response] = {}
        self._next = 0
        self._event = Event()
        self._error: BaseException | None = None

    async def put(self, priority: int, response: Response):
        """Add an item to the queue.

        Parameters
        ----------
        priority : int
            Priority of the request.
        response : Response
            The response to add to the queue.
        """
        self._responses[priority] = response

        if priority == self._next:
            # signal that the response the consumer is waiting for is ready
            self._event.set()

    def abort(self, error: BaseException):
        """Abort the queue, so that consumers stop waiting and raise instead.

        Parameters
        ----------
        error : BaseException
            The error that caused the abort.
        """
        self._error = error

        # wake up the consumer waiting for a response that will never arrive
        self._event.set()

    async def get_next(self) -> Response | None:
        """Get the next item from the queue based on priority.

        Returns
        -------
        Response | None
            The next item from the queue, or None if all have been consumed.
        """
        if self._error is not None:
            raise self._error

        if self._next >= self.total_size:
            return None

        while self._next not in self._responses:
            if self._error is not None:
                raise self._error

            self._event.clear()
            await self._event.wait()

        response = self._responses.pop(self._next)
        self._next += 1

        return response

    def empty(self) -> bool:
        """Whether the queue is empty."""
        return not self._responses
