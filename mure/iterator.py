import asyncio
from asyncio import Event, PriorityQueue, Task
from typing import AsyncIterator, Iterator

import orjson
from aiohttp import ClientSession

from mure.dtos import HistoricResponse, HTTPResource, Response
from mure.logging import Logger

LOGGER = Logger(__name__)


class ResponseIterator(Iterator[Response]):
    def __init__(
        self,
        resources: list[HTTPResource],
        *,
        batch_size: int = 5,
        log_errors: bool = True,
    ):
        """Initialize a response iteratoresponse.

        Parameters
        ----------
        resources : list[HTTPResource]
            Resources to request.
        batch_size : int, optional
            Number of resources to request in parallel, by default 5.
        log_errors : bool, optional
            True if Python errors should be logged, by default True.
        """
        self.resources = resources
        self.num_resources = len(resources)
        self.pending = len(resources)
        self.batch_size = batch_size

        self._log_errors = log_errors
        self._loop = asyncio.get_event_loop()
        self._queue = PriorityQueue()
        self._tasks = set()
        self._events = [Event() for _ in resources]
        self._responses = self._fetch_responses()

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

    def __iter__(self) -> Iterator[Response]:
        """Yield one response at a time.

        Yields
        ------
        Iterator[Response]
            Response iteratoresponse.
        """
        yield from self._responses

    def __next__(self) -> Response:
        """Return the next response.

        Returns
        -------
        Response
            Next response.
        """
        return next(self._responses)

    def _fetch_responses(self) -> Iterator[Response]:
        """Fetch responses in parallel.

        Yields
        ------
        Response
            One response at a time.
        """
        # get async generator
        responses = self._afetch_responses()

        # run the event loop until a response is available and yield it
        while True:
            try:
                yield self._loop.run_until_complete(anext(responses))
            except StopAsyncIteration:
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
        # fetch response
        response = await self._afetch(session, resource)

        # put response in the queue
        await self._queue.put((priority, response))

        # set event to notify that the response is ready
        event.set()

    def _fill_queue(self, tasks: Iterator[Task]):
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

    async def _afetch_responses(self) -> AsyncIterator[Response]:
        """Fetch responses in parallel.

        Yields
        ------
        Response
            The server's responses.
        """
        async with ClientSession() as session:
            # create tasks in the background (lazy)
            tasks = self._create_tasks(session)

            self._fill_queue(tasks)

            # fill the queue with tasks while yielding responses
            for event in self._events:
                # wait for the specific event to be set to preserve order of the resources
                await event.wait()

                self._fill_queue(tasks)

                # get response from the queue
                _, response = await self._queue.get()
                yield response

                self._queue.task_done()
                self.pending -= 1

                self._fill_queue(tasks)

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
                text = await response.text()
                return Response(
                    status=response.status,
                    reason=response.reason,  # type: ignore
                    ok=response.ok,
                    text=text,
                    url=response.url.human_repr(),
                    history=[
                        HistoricResponse(
                            status=h.status,
                            reason=h.reason,  # type: ignore
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
