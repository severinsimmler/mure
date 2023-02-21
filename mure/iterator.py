import asyncio
import itertools
from typing import Any, Iterable, Iterator

from aiohttp import ClientResponse, ClientSession

from mure.dtos import HistoricResponse, HTTPResource, Resource, Response
from mure.logging import Logger

LOGGER = Logger(__name__)


class ResponseIterator(Iterator[Response]):
    def __init__(
        self,
        resources: Iterable[Resource],
        *,
        batch_size: int = 5,
        log_errors: bool = True,
    ):
        """Initialize a response iterator.

        Parameters
        ----------
        resources : Iterable[Resource]
            Resources to request.
        batch_size : int, optional
            Number of resources to request in parallel, by default 5.
        log_errors : bool, optional
            True if Python errors should be logged, by default True.
        """
        self.resources = resources
        self.batch_size = batch_size
        self._log_errors = log_errors
        self._responses = self._process_batches()
        self._pending = len(resources) if isinstance(resources, list) else float("inf")

    def __repr__(self) -> str:
        """Response iterator representation.

        Returns
        -------
        str
            Representation with number of pending resources.
        """
        return f"<ResponseIterator: {self._pending} pending>"

    def __len__(self) -> int | float:
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

    async def _process_batch(self, resources: Iterable[HTTPResource]) -> list[Response]:
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
        async with ClientSession() as session:
            requests = [self._process(session, resource) for resource in resources]
            return await asyncio.gather(*requests)

    async def _process(self, session: ClientSession, resource: HTTPResource) -> Response:
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
        if not resource.get("url"):
            raise KeyError(f"'url' is missing in the given resource")

        if not resource.get("method"):
            raise KeyError(f"'method' is missing in the given resource")

        try:
            kwargs = {k: v for k, v in resource.items() if k not in {"method", "url"}}
            async with session.request(resource["method"], resource["url"], **kwargs) as response:
                response: ClientResponse
                text = await response.text()
                return Response(
                    status=response.status,
                    reason=response.reason,  # type: ignore
                    ok=response.ok,
                    text=text,
                    url=response.url.human_repr(),
                    history=[
                        HistoricResponse(
                            historic_response.status,
                            historic_response.reason,  # type: ignore
                            historic_response.ok,
                            historic_response.url.human_repr(),
                        )
                        for historic_response in response.history
                    ],
                )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)
            return Response(status=0, reason=repr(error), ok=False, text="", url="", history=[])

    @staticmethod
    def chunk(values: Iterable[Any], n: int = 5) -> Iterator[Any]:
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
        iterator = iter(values)
        for first in iterator:
            yield itertools.chain([first], itertools.islice(iterator, n - 1))
