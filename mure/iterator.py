import asyncio
import os
from asyncio import AbstractEventLoop, Event, Lock, PriorityQueue, Semaphore
from collections.abc import AsyncGenerator, Iterator
from typing import Self

import chardet
from httpx import AsyncClient

from mure.cache import Cache
from mure.logging import Logger
from mure.models import Request, Response

LOGGER = Logger(__name__)


class ResponseIterator(Iterator[Response]):
    """Response iterator that fetches responses concurrently."""

    def __init__(
        self,
        requests: list[Request],
        *,
        batch_size: int = 5,
        queue_size: int | None = None,
        cache: Cache | None = None,
    ):
        """Initialize a response iterator.

        Parameters
        ----------
        requests : list[Request]
            Resources to request.
        batch_size : int, optional
            Number of resources to request concurrently, by default 5.
        queue_size : int | None, optional
            Maximum number of responses to hold in the queue, by default None.
        cache : Cache | None, optional
            Cache to use for storing responses, by default None.
        """
        self.requests = requests
        self.num_requests = len(requests)
        self.pending = len(requests)
        self.batch_size = batch_size
        self.queue_size = queue_size
        self.cache = cache

        self._log_errors = bool(os.environ.get("MURE_LOG_ERRORS"))
        self._lock = Lock()
        self._http_semaphore = Semaphore(batch_size)
        self._queue_semaphore = Semaphore(queue_size or len(requests))
        self._events = [Event() for _ in requests]
        self._tasks = []
        self._queue = PriorityQueue()
        self._responses = self._fetch_responses()

    def __repr__(self) -> str:
        """Response iterator representation.

        Returns
        -------
        str
            Representation with number of pending requests.
        """
        return f"<ResponseIterator: {self.pending}/{self.num_requests} pending>"

    def __len__(self) -> int | float:
        """Return the number of pending responses.

        Returns
        -------
        int
            Absolute number of pending responses.
        """
        return self.pending

    def __iter__(self) -> Self:
        """Yield one response at a time.

        Yields
        ------
        Iterator[Response]
            Response iterator.
        """
        return self

    def __next__(self) -> Response:
        """Return the next response.

        Returns
        -------
        Response
            Next response.
        """
        return next(self._responses)

    def _fetch_responses(self) -> Iterator[Response]:
        """Fetch responses concurrently.

        Yields
        ------
        Response
            One response at a time.
        """
        # create and set a new event loop that is used for all operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        agenerator = self._agenerator_wrapper(loop)

        # run the event loop until a response is available and yield it
        while True:
            try:
                yield loop.run_until_complete(anext(agenerator))
            except StopAsyncIteration:
                break

        # cleanup the event loop
        asyncio.set_event_loop(None)

    def _schedule_tasks(self, session: AsyncClient, loop: AbstractEventLoop):
        """Schedule tasks for fetching responses concurrently.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        loop : AbstractEventLoop
            Event loop to use.
        """
        for priority, request in enumerate(self.requests):
            coroutine = self._aprocess_request(
                session,
                priority,
                request,
                self._events[priority],
            )
            self._tasks.append(loop.create_task(coroutine))

    async def _aprocess_request(
        self,
        session: AsyncClient,
        priority: int,
        request: Request,
        event: Event,
    ):
        """Process a request by fetching and putting it in the queue.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        priority : int
            Priority of the request.
        request. : Request
            Resource to request.
        event : Event
            Event to set when the response is ready.
        """
        async with self._queue_semaphore:
            LOGGER.debug(f"Started {priority}")

            # if cache is given and has response for the request, use it
            if self.cache and self.cache.has(request):
                LOGGER.debug(f"Found response {priority} in cache")
                async with self._lock:
                    response = self.cache.get(request)
                LOGGER.debug(f"Used response {priority} from cache")
            else:
                response = await self._asend_request(session, request)

                # save response to cache
                if self.cache:
                    LOGGER.debug(f"Saving response {priority} in cache")
                    async with self._lock:
                        self.cache.set(request, response)
                    LOGGER.debug(f"Saved response {priority} in cache")

            # put response in the queue
            await self._queue.put((priority, response))

            # set event to notify that the response is ready
            event.set()

            LOGGER.debug(f"Finished {priority}")

    async def _agenerator_wrapper(self, loop: AbstractEventLoop) -> AsyncGenerator[Response, None]:
        """Wrap the response generator.

        Parameters
        ----------
        loop : AbstractEventLoop
            Event loop to use.

        Yields
        ------
        Response
            The server's response.
        """
        async for response in self._afetch_responses(loop):
            yield response

    async def _afetch_responses(self, loop: AbstractEventLoop) -> AsyncGenerator[Response, None]:
        """Fetch responses concurrently.

        Parameters
        ----------
        loop : AbstractEventLoop
            Event loop to use.

        Yields
        ------
        Response
            The server's response.
        """
        try:
            async with AsyncClient(follow_redirects=True) as session:
                # schedule tasks for fetching responses concurrently
                self._schedule_tasks(session, loop)

                for event in self._events:
                    # wait for the specific event to be set to preserve order of the requests
                    await event.wait()

                    # get response from the queue
                    priority, response = await self._queue.get()
                    self._queue.task_done()

                    LOGGER.debug(f"Yielding {priority}")
                    yield response
                    self.pending -= 1
        except GeneratorExit:
            return

    async def _asend_request(self, session: AsyncClient, request: Request) -> Response:
        """Perform a HTTP request.

        Parameters
        ----------
        session : ClientSession
            HTTP session to use.
        request : Resource
            Resource to request.

        Returns
        -------
        Response
            The server's response.
        """
        try:
            # acquire semaphore to limit the number of concurrent requests
            async with self._http_semaphore:
                LOGGER.debug("Sending request")
                response = await session.request(
                    request.method,
                    request.url,
                    headers=request.headers,
                    params=request.params,
                    data=request.data,
                    json=request.json,
                    timeout=request.timeout,
                )

            content = await response.aread()

            try:
                text = content.decode(response.encoding or "utf-8", errors="replace")
            except (LookupError, TypeError):
                # LookupError is raised if the encoding was not found which could
                # indicate a misspelling or similar mistake
                #
                # TypeError can be raised if encoding is None
                encoding = chardet.detect(content)["encoding"]
                text = content.decode(encoding or "utf-8", errors="replace")

            return Response(
                status=response.status_code,
                reason=response.reason_phrase,
                ok=response.is_success,
                text=text,
                url=str(response.url),
            )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)

            return Response(status=0, reason=repr(error), ok=False, text="", url="")
