import asyncio
from asyncio import Event, PriorityQueue, Task
from typing import AsyncGenerator, Iterator, Self

import chardet
import orjson
from aiohttp import ClientSession

from mure.dtos import HistoricResponse, HTTPResource, Response
from mure.logging import Logger

LOGGER = Logger(__name__)


class ResponseIterator(Iterator[Response]):
    """Response iterator that fetches responses concurrently."""

    def __init__(
        self,
        resources: list[HTTPResource],
        *,
        batch_size: int = 5,
        log_errors: bool = True,
    ):
        """Initialize a response iterator.

        Parameters
        ----------
        resources : list[HTTPResource]
            Resources to request.
        batch_size : int, optional
            Number of resources to request concurrently, by default 5.
        log_errors : bool, optional
            True if Python errors should be logged, by default True.
        """
        self.resources = resources
        self.num_resources = len(resources)
        self.pending = len(resources)
        self.batch_size = batch_size

        self._log_errors = log_errors
        self._loop = asyncio.new_event_loop()
        self._queue = PriorityQueue()
        self._events = [Event() for _ in resources]
        self._tasks: set[Task] = set()
        self._responses = self._fetch_responses()
        self._generator = None

    def __repr__(self) -> str:
        """Response iterator representation.

        Returns
        -------
        str
            Representation with number of pending resources.
        """
        return f"<ResponseIterator: {self.pending}/{self.num_resources} pending>"

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
        if self._generator:
            self._loop.run_until_complete(self._generator.aclose())

        if self._tasks:
            for task in self._tasks:
                task.cancel()
            self._loop.run_until_complete(asyncio.gather(*self._tasks, return_exceptions=True))

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
        for i, (resource, event) in enumerate(zip(self.resources, self._events)):
            # create task in the background
            yield self._loop.create_task(self._aprocess_resource(i, session, resource, event))

    async def _aprocess_resource(
        self,
        priority: int,
        session: ClientSession,
        resource: HTTPResource,
        event: Event,
    ):
        """Process a resource by fetching and putting it in the queue.

        Parameters
        ----------
        priority : int
            Priority of the resource.
        session : ClientSession
            Client session to use.
        resource : HTTPResource
            Resource to request.
        event : Event
            Event to set when the response is ready.
        """
        LOGGER.debug(f"Started {priority}")

        # fetch response
        response = await self._afetch(session, resource)

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
        async with ClientSession() as session:
            # create tasks (lazy)
            tasks = self._create_tasks(session)

            # process first batch of tasks
            self._process_batch(tasks)

            for event in self._events:
                # wait for the specific event to be set to preserve order of the resources
                await event.wait()

                # process next batch of tasks
                self._process_batch(tasks)

                # get response from the queue
                i, response = await self._queue.get()

                # process next batch of tasks
                self._process_batch(tasks)

                yield response
                self._queue.task_done()
                self.pending -= 1

    async def _afetch(self, session: ClientSession, resource: HTTPResource) -> Response:
        """Perform a HTTP request.

        Parameters
        ----------
        session : ClientSession
            Client session to use.
        resource : Resource
            Resource to request.

        Returns
        -------
        Response
            The server's response.
        """
        try:
            kwargs = {k: v for k, v in resource.items() if k not in {"method", "url"}}

            # orjson.dumps() is faster than json.dumps() which is used by default
            if kwargs.get("json") and not kwargs.get("data"):
                kwargs["data"] = orjson.dumps(kwargs.pop("json"))

            async with session.request(resource["method"], resource["url"], **kwargs) as response:
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
                    text = content.decode(encoding, errors="replace")

                return Response(
                    status=response.status,
                    reason=response.reason,
                    ok=response.ok,
                    text=text,
                    url=response.url.human_repr(),
                    history=[
                        HistoricResponse(
                            status=h.status,
                            reason=h.reason,
                            ok=h.ok,
                            url=h.url.human_repr(),
                        )
                        for h in response.history
                    ],
                )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)

            return Response(status=0, reason=repr(error), ok=False, text="", url="", history=[])
