import asyncio
from asyncio import PriorityQueue, Task
from typing import Iterable, Iterator

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
        self.num_resources = len(resources)
        self.pending = len(resources)
        self.batch_size = batch_size
        self.batches = [
            resources[i : i + self.batch_size]
            for i in range(0, self.num_resources, self.batch_size)
        ]

        self._log_errors = log_errors
        self._queue = PriorityQueue(maxsize=2)  # do not keep more than 2 batches in memory
        self._tasks: set[Task] = set()
        self._responses = self._fetch_batches()

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

    def _fetch_batches(self):
        try:
            # construct a new event loop
            loop = asyncio.new_event_loop()

            # set the new event loop as the current one
            asyncio.set_event_loop(loop)

            # fetch responses in parallel
            results = self._afetch_batches()
            while True:
                try:
                    yield loop.run_until_complete(results.__anext__())
                except StopAsyncIteration:
                    break
        finally:
            if self._tasks:
                # cancel all tasks if any left
                for task in self._tasks:
                    task.cancel()

                # wait until all tasks are cancelled
                loop.run_until_complete(asyncio.gather(*self._tasks, return_exceptions=True))

            # close the event loop
            asyncio.set_event_loop(None)
            loop.close()

    def _start_fetching(
        self,
        priority: int,
        session: ClientSession,
        resources: Iterable[HTTPResource],
    ):
        # create task in the background
        task = asyncio.create_task(self._afetch_batch(priority, session, resources))

        # keep track of the task
        self._tasks.add(task)

        # and remove task when it's done
        task.add_done_callback(self._tasks.discard)

    async def _afetch_batches(self):
        async with ClientSession() as session:
            # start processing the first batch in the background
            self._start_fetching(0, session, self.batches[0])

            for i, batch in enumerate(self.batches[1:], start=1):
                # start processing the next batch
                self._start_fetching(i, session, batch)

                # get results of the previous batch from the queue and yield them
                _, responses = await self._queue.get()
                for response in responses:
                    yield response
                    self.pending -= 1

            # yield results of the last batch from the queue (if any)
            while not self._queue.empty():
                _, responses = await self._queue.get()
                for response in responses:
                    yield response
                    self.pending -= 1

    async def _afetch_batch(
        self,
        priority: int,
        session: ClientSession,
        resources: Iterable[HTTPResource],
    ):
        """Fetch each resource in the given batch and put responses in the queue.

        Parameters
        ----------
        priority : int
            Priority of the batch.
        resource : HTTPResource
            Resource to request.

        Returns
        -------
        list[Response]
            The server's responses for each resource.
        """
        # create coroutines for each resource
        coroutines = [self._afetch(session, resource) for resource in resources]

        # fetch responses in parallel
        responses = await asyncio.gather(*coroutines)

        # put responses in the queue
        await self._queue.put((priority, responses))

    async def _afetch(self, session: ClientSession, resource: HTTPResource) -> Response:
        """Perform HTTP request.

        Parameters
        ----------
        resource : Resource
            Resource to request.

        Returns
        -------
        Response
            The server's response.
        """
        if not resource.get("url"):
            raise KeyError("'url' is missing in the given resource")

        if not resource.get("method"):
            raise KeyError("'method' is missing in the given resource")

        try:
            kwargs = {k: v for k, v in resource.items() if k not in {"method", "url"}}

            # orjson.dumps() is faster than json.dumps() which is used by default
            if kwargs.get("json") and not kwargs.get("data"):
                kwargs["data"] = orjson.dumps(kwargs.pop("json"))

            async with session.request(resource["method"], resource["url"], **kwargs) as response:
                return Response(
                    status=response.status,
                    reason=response.reason,  # type: ignore
                    ok=response.ok,
                    text=await response.text(),
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
