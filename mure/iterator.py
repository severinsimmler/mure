import asyncio
import contextlib
import os
from asyncio import AbstractEventLoop, Event, PriorityQueue, Task
from collections.abc import AsyncGenerator, Iterator
from typing import Self

import chardet
import httpcore
from hishel import AsyncCacheClient
from hishel._utils import generate_key
from httpx import AsyncClient

from mure.cache import Cache, CacheController, get_storage
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
        cache: Cache | None = None,
    ):
        """Initialize a response iterator.

        Parameters
        ----------
        requests : list[Request]
            Resources to request.
        batch_size : int, optional
            Number of resources to request concurrently, by default 5.
        cache : Cache | None, optional
            Cache to use for storing responses, by default None.
        """
        self.requests = requests
        self.num_requests = len(requests)
        self.pending = len(requests)
        self.batch_size = batch_size

        self._storage = get_storage(cache) if cache else None
        self._log_errors = bool(os.environ.get("MURE_LOG_ERRORS"))
        self._queue = PriorityQueue()
        self._events = [Event() for _ in requests]
        self._tasks: dict[int, Task] = {}
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
        # get new event loop that is used for all operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            agenerator = self._agenerator_wrapper(loop)

            while True:
                try:
                    yield loop.run_until_complete(anext(agenerator))
                except StopAsyncIteration:
                    break
        finally:
            if not loop.is_closed():
                loop.close()

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

            self._tasks[priority] = loop.create_task(coroutine)
            yield

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
        LOGGER.debug(f"Started {priority}")

        response = await self._asend_request(session, request)

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
            async with (
                AsyncClient(follow_redirects=True, http2=True)
                if self._storage is None
                else AsyncCacheClient(
                    follow_redirects=True,
                    http2=True,
                    storage=self._storage,
                    controller=CacheController(),
                )
            ) as session:
                # schedule tasks for fetching responses concurrently
                tasks = self._schedule_tasks(session, loop)
                while len(self._tasks) < self.batch_size:
                    try:
                        next(tasks)
                    except StopIteration:
                        break

                for event in self._events:
                    # wait for the specific event to be set to preserve order of the requests
                    await event.wait()

                    # get response from the queue
                    priority, response = await self._queue.get()

                    # get rid of the task that has been completed
                    self._tasks.pop(priority)

                    LOGGER.debug(f"Yielding {priority}")
                    yield response
                    self.pending -= 1

                    self._queue.task_done()

                    with contextlib.suppress(StopIteration):
                        # schedule next task (if any left)
                        next(tasks)
        except GeneratorExit:
            return
        finally:
            await asyncio.sleep(0.5)
            await self._queue.join()

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
        _request = session.build_request(
            method=request.method,
            url=request.url,
            data=request.data,
            json=request.json,
            params=request.params,
            headers=request.headers,
            timeout=request.timeout,
        )

        try:
            LOGGER.debug("Sending request")
            # perform the request
            response = await session.send(_request, follow_redirects=session.follow_redirects)

            # read the response content
            content = await response.aread()

            try:
                # try to decode the content using the response encoding
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
                content=content,
                url=str(response.url),
            )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)

            if self._storage is not None:
                cached_request = httpcore.Request(
                    method=_request.method,
                    url=str(_request.url),
                    headers=_request.headers,  # type: ignore
                    content=_request.content,
                )
                cached_response = httpcore.Response(
                    status=0,
                    content=b"",
                    extensions={"reason_phrase": repr(error).encode("utf-8")},
                )
                cached_response.read()

                await self._storage.store(
                    key=generate_key(cached_request, _request.content),
                    request=cached_request,
                    response=cached_response,
                )

            return Response(status=0, reason=repr(error), ok=False, text="", url="", content=b"")
