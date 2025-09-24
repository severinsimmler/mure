import asyncio
import contextlib
from asyncio import CancelledError, Event, PriorityQueue, Semaphore
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

import chardet
from hishel import AsyncCacheClient
from hishel._utils import generate_key
from httpcore import Request as _Request
from httpcore import Response as _Response
from httpx import AsyncClient, Headers

from mure.cache import Cache, CacheController, get_storage
from mure.logging import Logger
from mure.models import Request, Response

LOGGER = Logger(__name__)


class AsyncResponseIterator(AsyncIterator[Response]):
    """Iterator that fetches responses concurrently."""

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
        self.consumed = 0
        self.batch_size = batch_size
        self._storage = get_storage(cache) if cache else None
        self._queue = PriorityQueue()
        self._semaphore = Semaphore(batch_size)
        self._events = [Event() for _ in requests]
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
        response = await self._aget_response(self.consumed)

        if response is None:
            raise StopAsyncIteration

        self.consumed += 1
        self.pending -= 1

        return response

    async def _aget_response(self, priority: int) -> Response | None:
        """Return the response for the given priority (or None if done).

        Note
        ----
        Schedules the fetching task first if it hasn't been started yet.

        Parameters
        ----------
        priority : int
            Priority of the request to fetch.

        Returns
        -------
        Response | None
            The next response, or None if there are no more responses to fetch.
        """
        if self._task is None:
            self._task = asyncio.create_task(self._afetch_responses())

        if self._task.done() and self._queue.empty():
            return None

        try:
            LOGGER.debug(f"Waiting for response with priority {priority}")

            # wait for the response to be ready...
            await self._events[priority].wait()

            # ...now actually get it
            _, response = await self._queue.get()

            LOGGER.debug(f"Received response with priority {priority}")

            return response
        except Exception:
            if not self._task.done():
                self._task.cancel()
            raise

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

    async def _asend_request(self, session: AsyncClient, request: Request) -> Response:
        """Perform an HTTP request.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        request : Request
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
            timeout=request.timeout or 30,
        )

        try:
            # send the request...
            response = await session.send(_request, follow_redirects=session.follow_redirects)

            # ...and read the content
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
                headers=response.headers,
            )
        except Exception as error:
            if self._storage is not None:
                cached_request = _Request(
                    method=_request.method,
                    url=str(_request.url),
                    headers=_request.headers,  # type: ignore
                    content=_request.content,
                )
                cached_response = _Response(
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

            return Response(
                status=0,
                reason=repr(error),
                ok=False,
                text="",
                url="",
                content=b"",
                headers=Headers(),
            )

    async def _afetch_response(
        self,
        session: AsyncClient,
        priority: int,
        request: Request,
    ):
        """Fetch a single response with semaphore control.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        priority : int
            Priority of the request.
        request : Request
            Resource to request.
        """
        async with self._semaphore:
            LOGGER.debug(f"Fetching response with priority {priority}")

            response = await self._asend_request(session, request)

            LOGGER.debug(f"Fetched response with priority {priority}")

        await self._queue.put((priority, response))

        # signal that the response is ready
        self._events[priority].set()

    async def _afetch_responses(self):
        """Fetch all responses concurrently."""
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
            tasks = [
                self._afetch_response(session, priority, request)
                for priority, request in enumerate(self.requests)
            ]
            await asyncio.gather(*tasks)
