import asyncio
import os
from asyncio import Event, PriorityQueue, Task
from collections.abc import AsyncGenerator, Iterator
from typing import Self

import chardet
from aiohttp import ClientSession

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
        self.cache = cache

        self._log_errors = bool(os.environ.get("MURE_LOG_ERRORS"))
        self._loop = asyncio.new_event_loop()
        self._queue = PriorityQueue()
        self._events = [Event() for _ in requests]
        self._tasks: set[Task] = set()
        self._responses = self._fetch_responses()
        self._generator = None

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

    def __del__(self):
        """Cancel open tasks (if any) and close the event loop."""
        self._cleanup()

    def _cleanup(self):
        """Cancel open tasks (if any) and close the event loop."""
        if self._loop.is_closed():
            return

        if self._generator:
            self._loop.run_until_complete(self._generator.aclose())

        # cancel pending tasks (if any)
        if tasks := {
            task
            for task in self._tasks | asyncio.all_tasks(self._loop)
            if not task.done() or task.cancelled()
        }:
            for task in tasks:
                task.cancel()
            self._loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

        if not self._loop.is_closed():
            self._loop.close()
            asyncio.set_event_loop(None)

    def _fetch_responses(self) -> Iterator[Response]:
        """Fetch responses concurrently.

        Yields
        ------
        Response
            One response at a time.
        """
        asyncio.set_event_loop(self._loop)

        # set async generator
        self._generator = self._afetch_responses()

        # run the event loop until a response is available and yield it
        while True:
            try:
                yield self._loop.run_until_complete(anext(self._generator))
            except StopAsyncIteration:
                self._cleanup()
                break

    def _create_tasks(self, session: ClientSession) -> Iterator[Task]:
        """Create tasks for each resource.

        Parameters
        ----------
        session : ClientSession
            Client session to use.

        Yields
        ------
        Iterator[Task]
            Tasks to fetch resources.
        """
        for i, (request, event) in enumerate(zip(self.requests, self._events, strict=False)):
            # create task in the background
            yield self._loop.create_task(self._aprocess_request(i, session, request, event))

    async def _aprocess_request(
        self,
        priority: int,
        session: ClientSession,
        request: Request,
        event: Event,
    ):
        """Process a request by fetching and putting it in the queue.

        Parameters
        ----------
        priority : int
            Priority of the request.
        session : ClientSession
            Client session to use.
        request. : Request
            Resource to request.
        event : Event
            Event to set when the response is ready.
        """
        LOGGER.debug(f"Started {priority}")

        # if cache is given and has the request., use it
        if self.cache and self.cache.has(request):
            LOGGER.debug("Found response in cache")
            response = self.cache.get(request)
        else:
            response = await self._afetch(session, request)

            # save response to cache
            if self.cache:
                self.cache.set(request, response)
                LOGGER.debug("Saved response to cache")

        # put response in the queue
        await self._queue.put((priority, response))

        # set event to notify that the response is ready
        event.set()

        LOGGER.debug(f"Finished {priority}")

    def _process_batch(self, tasks: Iterator[Task]):
        """Fill the queue with tasks.

        Parameters
        ----------
        tasks : Iterator[Task]
            Tasks to put in the queue.
        """
        if len(self._tasks) < self.batch_size:
            for task in tasks:
                # keep track of the task
                self._tasks.add(task)

                # and remove task when it's done
                task.add_done_callback(self._tasks.remove)

                if len(self._tasks) >= self.batch_size:
                    break

    async def _afetch_responses(self) -> AsyncGenerator[Response, None]:
        """Fetch responses concurrently.

        Yields
        ------
        Response
            The server's response.
        """
        try:
            # one session for all requests
            session = ClientSession(loop=self._loop)

            # create tasks (lazy)
            tasks = self._create_tasks(session)

            # process first batch of tasks
            self._process_batch(tasks)

            for event in self._events:
                # wait for the specific event to be set to preserve order of the requests
                await event.wait()

                # process next batch of tasks
                self._process_batch(tasks)

                # get response from the queue
                _, response = await self._queue.get()

                # process next batch of tasks
                self._process_batch(tasks)

                yield response
                self._queue.task_done()
                self.pending -= 1
        except GeneratorExit:
            return
        finally:
            await session.close()

    async def _afetch(self, session: ClientSession, request: Request) -> Response:
        """Perform a HTTP request.

        Parameters
        ----------
        session : ClientSession
            Client session to use.
        request : Resource
            Resource to request.

        Returns
        -------
        Response
            The server's response.
        """
        try:
            async with session.request(
                request.method,
                request.url,
                headers=request.headers,
                params=request.params,
                data=request.data,
                json=request.json,
                timeout=request.timeout,
            ) as response:
                content = await response.read()
                encoding = response.get_encoding()

                try:
                    text = content.decode(encoding, errors="replace")
                except (LookupError, TypeError):
                    # LookupError is raised if the encoding was not found which could
                    # indicate a misspelling or similar mistake
                    #
                    # TypeError can be raised if encoding is None
                    encoding = chardet.detect(content)["encoding"]
                    text = content.decode(encoding or "utf-8", errors="replace")

                return Response(
                    status=response.status,
                    reason=response.reason,
                    ok=response.ok,
                    text=text,
                    url=response.url.human_repr(),
                )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)

            return Response(status=0, reason=repr(error), ok=False, text="", url="")
