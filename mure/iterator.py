import asyncio
import contextlib
import os
from asyncio import CancelledError, Semaphore, TaskGroup
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

from httpx import AsyncClient

from mure.cache import ResponseStorage
from mure.logging import Logger
from mure.models import Request, Response
from mure.queue import Queue

LOGGER = Logger(__name__)


class AsyncResponseIterator(AsyncIterator[Response]):
    """Iterator that fetches responses concurrently."""

    def __init__(
        self,
        requests: list[Request],
        *,
        batch_size: int = 5,
        enable_cache: bool = False,
    ):
        """Initialize a response iterator.

        Parameters
        ----------
        requests : list[Request]
            Resources to request.
        batch_size : int, optional
            Number of resources to request concurrently, by default 5.
        enable_cache : bool, optional
            Whether to use a cache for storing responses, by default False.
        """
        self.requests = requests
        self.num_requests = len(requests)
        self.batch_size = batch_size
        self._storage = ResponseStorage() if enable_cache else None
        self._log_errors = bool(os.environ.get("MURE_LOG_ERRORS"))
        self._queue = Queue(self.num_requests)
        self._semaphore = Semaphore(self.batch_size)
        self._task = None

    def __aiter__(self) -> Self:
        """Return the async iterator."""
        return self

    async def __anext__(self) -> Response:
        """Return the next response (or raise StopAsyncIteration).

        Returns
        -------
        Response
            The next response.

        Raises
        ------
        StopAsyncIteration
            If there are no more responses to fetch.
        """
        response = await self.aconsume_next_response()

        if response is None:
            raise StopAsyncIteration

        return response

    async def __aenter__(self):
        """Enter async context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        """Exit async context."""
        await self.aclose()

    async def aclose(self):
        """Clean up resources."""
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(CancelledError):
                await self._task

    async def aconsume_next_response(self) -> Response | None:
        """Consume the next response.

        Parameters
        ----------
        priority : int
            Priority of the request to consume.

        Returns
        -------
        Response | None
            Next response, or None if there are no more responses to consume.
        """
        if self._storage is not None and not self._storage.exists:
            # make sure the storage is set up and exists
            await self._storage.asetup()

        if self._task is None:
            self._task = asyncio.create_task(self._afetch_responses())

        if self._task.done() and self._queue.empty():
            return None

        return await self._queue.get_next()

    async def _asend_request(
        self,
        session: AsyncClient,
        request: Request,
        priority: int,
    ) -> Response:
        """Perform an HTTP request.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        request : Request
            Resource to request.
        priority : int
            Priority of the request.

        Returns
        -------
        Response
            The server's response.
        """
        if self._storage is not None and (response := await self._storage.aget_response(request)):
            return response

        _request = session.build_request(
            method=request.method,
            url=request.url,
            data=request.data,
            json=request.json,
            params=request.params,
            headers=request.headers,
            timeout=request.timeout or 30,
        )

        try:
            async with self._semaphore:
                LOGGER.debug(f"Start firing request with priority {priority}")

                # send the request...
                response = await session.send(_request, follow_redirects=session.follow_redirects)

                LOGGER.debug(f"Finished firing request with priority {priority}")

            # ...and read the content
            content = await response.aread()

            response = Response(
                status=response.status_code,
                reason=response.reason_phrase,
                ok=response.is_success,
                content=content,
                encoding=response.encoding,
                url=str(response.url),
                headers=dict(response.headers),
            )
        except Exception as error:
            if self._log_errors:
                LOGGER.error(error)

            response = Response(
                status=0,
                reason=repr(error),
                ok=False,
                url="",
                content=b"",
                encoding="utf-8",
                headers={},
            )

        if self._storage is not None:
            await self._storage.asave_response(request, response)

        return response

    async def _afetch_response(
        self,
        session: AsyncClient,
        priority: int,
        request: Request,
    ):
        """Fetch a single response.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        priority : int
            Priority of the request.
        request : Request
            Resource to request.
        """
        response = await self._asend_request(session, request, priority)

        await self._queue.put(priority, response)

    async def _afetch_responses(self):
        """Fetch all responses concurrently."""
        async with AsyncClient(follow_redirects=True, http2=True) as session, TaskGroup() as tg:
            for priority, request in enumerate(self.requests):
                LOGGER.debug(f"Scheduling request with priority {priority}")
                tg.create_task(self._afetch_response(session, priority, request))
