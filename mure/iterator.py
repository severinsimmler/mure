import asyncio
from asyncio import PriorityQueue
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
        """Initialize a response iterator.

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
        self._loop = asyncio.get_event_loop()
        self._queue = PriorityQueue(maxsize=2)  # do not keep more than 2 batches in memory
        self._session = ClientSession(loop=self._loop)
        self._responses = self._process_batches()

    def __del__(self):
        """Close the current HTTP session."""
        if not self._session.closed:
            self._loop.run_until_complete(self._session.close())

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
            Response iterator.
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

    def _process_batches(self) -> Iterator[Response]:
        """Process batches and yield responses one by one.

        Yields
        ------
        Iterator[Response]
            Response iterator.
        """
        # start processing the first batch in the background
        self._loop.create_task(self._aprocess_batch(0, self.batches[0]))

        for i, batch in enumerate(self.batches[1:], start=1):
            # start processing the next batch in the background
            self._loop.create_task(self._aprocess_batch(i, batch))

            # yield results of the previous batch from the queue
            for response in self._loop.run_until_complete(self._queue.get())[1]:
                yield response
                self.pending -= 1

        # yield results of the last batch from the queue (if any)
        while not self._queue.empty():
            for response in self._loop.run_until_complete(self._queue.get())[1]:
                yield response
                self.pending -= 1

    async def _aprocess_batch(self, priority: int, resources: Iterable[HTTPResource]):
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
        # fetch responses in parallel
        responses = await asyncio.gather(*[self._aprocess(resource) for resource in resources])

        # put responses in the queue
        await self._queue.put((priority, responses))

    async def _aprocess(self, resource: HTTPResource) -> Response:
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

            async with self._session.request(resource["method"], resource["url"], **kwargs) as r:
                return Response(
                    status=r.status,
                    reason=r.reason,  # type: ignore
                    ok=r.ok,
                    text=await r.text(),
                    url=r.url.human_repr(),
                    history=[
                        HistoricResponse(
                            status=h.status,
                            reason=h.reason,  # type: ignore
                            ok=h.ok,
                            url=h.url.human_repr(),
                        )
                        for h in r.history
                    ],
                )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)

            return Response(status=0, reason=repr(error), ok=False, text="", url="", history=[])
