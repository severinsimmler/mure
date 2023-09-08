import asyncio
from itertools import islice
from typing import AsyncGenerator, Iterable, Iterator

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
        self.resources = resources
        self.batch_size = batch_size

        self._log_errors = log_errors
        self._loop = asyncio.get_event_loop()
        self._session = ClientSession(loop=self._loop)
        self._responses = self._process_batches()
        self._pending = len(resources)

    def __del__(self):
        """Close the current HTTP session and event loop."""
        self._loop.run_until_complete(self._session.close())
        self._loop.close()

    def __repr__(self) -> str:
        """Response iterator representation.

        Returns
        -------
        str
            Representation with number of pending resources.
        """
        return f"<ResponseIterator: {self._pending}/{len(self.resources)} pending>"

    def __len__(self) -> int | float:
        """Return the number of pending responses.

        Returns
        -------
        int
            Absolute number of pending responses.
        """
        return self._pending

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

    @property
    def batches(self) -> Iterator[list[HTTPResource]]:
        """Split the resources into batches of size `batch_size`.

        Yields
        ------
        list[HTTPResource]
            One batch at a time.
        """
        iterator = iter(self.resources)
        while True:
            batch = list(islice(iterator, self.batch_size))
            if not batch:
                return
            yield batch

    def _process_batches(self) -> Iterator[Response]:
        """Process batches synchronously and yield responses one by one.

        Yields
        ------
        Iterator[Response]
            Response iterator.
        """
        aiterator = self._aprocess_batches().__aiter__()

        async def _fetch_next() -> list[Response]:
            try:
                return await aiterator.__anext__()
            except StopAsyncIteration:
                return []

        for _ in self.batches:
            for response in self._loop.run_until_complete(_fetch_next()):
                yield response
                self._pending -= 1
                # TODO trigger fetching the next batch after yielding the first response

    async def _aprocess_batches(self) -> AsyncGenerator[list[Response], None]:
        """Process batches asynchronously and return responses batch by batch.

        Yields
        ------
        list[Response]
            Batch of responses.
        """
        for batch in self.batches:
            yield await self._aprocess_batch(batch)

    async def _aprocess_batch(self, resources: Iterable[HTTPResource]) -> list[Response]:
        """Perform HTTP request for each resource in the given batch.

        Parameters
        ----------
        resource : HTTPResource
            Resource to request.

        Returns
        -------
        list[Response]
            The server's responses for each resource.
        """
        return await asyncio.gather(*[self._aprocess(resource) for resource in resources])

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
