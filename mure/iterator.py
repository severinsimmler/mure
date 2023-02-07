import asyncio
from typing import Any, Iterable, Iterator

from aiohttp import ClientSession

from mure.dtos import Resource, Response
from mure.logging import Logger

LOGGER = Logger(__name__)


class ResponseIterator(Iterator):
    def __init__(self, resources: Iterable[Resource], *, batch_size: int = 5):
        """Initialize a response iterator.

        Parameters
        ----------
        resources : Iterable[Resource]
            Resources to request.
        batch_size : int, optional
            Number of resources to request in parallel, by default 5.
        """
        self.resources = resources
        self.batch_size = batch_size
        self._responses = self._process_batches()
        self._pending = len(resources)

    def __repr__(self) -> str:
        """Response iterator representation.

        Returns
        -------
        str
            Representation with number of pending resources.
        """
        return f"<ResponseIterator: {self._pending} pending>"

    def __len__(self) -> int:
        """Return the number of resources/responses.

        Returns
        -------
        int
            Absolute number of resources/responses.
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
        """Returns the next response.

        Returns
        -------
        Response
            Next response.
        """
        return next(self._responses)

    def _process_batches(self) -> Iterator[Response]:
        """Processes all batches.

        Yields
        ------
        Iterator[Response]
            One response at a time.
        """
        for batch in self.chunk(self.resources, n=self.batch_size):
            for response in asyncio.run(self._process_batch(batch)):
                self._pending -= 1
                yield response

    async def _process_batch(self, resources: Iterable[Resource]) -> list[Response]:
        """Perform HTTP request for each resource in the given batch.

        Parameters
        ----------
        resource : Resource
            Resource to request.

        Returns
        -------
        list[Response]
            The server's responses for each resource.
        """
        async with ClientSession() as session:
            requests = [self._process(session, resource) for resource in resources]
            return await asyncio.gather(*requests)

    @staticmethod
    async def _process(session: ClientSession, resource: Resource) -> Response:
        """Perform HTTP request.

        Parameters
        ----------
        session : ClientSession
            First-class interface for making HTTP requests.
        resource : Resource
            Resource to request.

        Returns
        -------
        Response
            The server's response.
        """
        try:
            method = resource.pop("method")
            url = resource.pop("url")
        except KeyError as error:
            raise KeyError(f"{error} is not defined for the given resource")

        try:
            async with session.request(method, url, **resource) as response:
                text = await response.text()
                return Response(
                    status=response.status,
                    reason=response.reason,
                    ok=response.ok,
                    text=text,
                )
        except Exception as error:
            LOGGER.error(error)
            return Response(status=0, reason=repr(error), ok=False, text="")

    @staticmethod
    def chunk(values: list[Any], n: int = 5) -> Iterator[Any]:
        """Splits the given list of values into batches of size `n`.

        Parameters
        ----------
        values : list[Any]
            Values to chunk.
        n : int, optional
            Number of items per batch, by default 5.

        Yields
        ------
        Iterator[Any]
            One batch at a time.
        """
        for i in range(0, len(values), n):
            yield values[i : i + n]
