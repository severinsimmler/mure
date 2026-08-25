import asyncio
import contextlib
import os
from asyncio import CancelledError, Task, TaskGroup
from collections.abc import AsyncIterator, Iterator
from types import TracebackType
from typing import Self

from httpx2 import AsyncClient, Limits

from mure.cache import Cache, get_storage
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
        cache: Cache | None = None,
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
        self._storage = get_storage(cache)
        self._log_errors = bool(os.environ.get("MURE_LOG_ERRORS"))
        self._queue = Queue(self.num_requests)
        self._task = None
        self._is_cleaned_up = False

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
            await self.acleanup()
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
        await self.acleanup()

    async def acleanup(self):
        """Clean up resources."""
        if self._is_cleaned_up:
            return

        self._is_cleaned_up = True

        if self._task and not self._task.done():
            # if every response has been consumed, the task is only closing its HTTP
            # session, which should not be interrupted
            if not self._queue.is_exhausted:
                self._task.cancel()

            with contextlib.suppress(CancelledError):
                await self._task

        if self._storage is not None:
            # the consumer may stop iterating at any time (e.g. by breaking out of the
            # loop), which cancels this task; closing the storage must not be
            # interrupted halfway through, otherwise connections are left dangling
            task = asyncio.create_task(self._storage.acleanup())

            try:
                await asyncio.shield(task)
            except CancelledError:
                await task
                raise

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
            self._task.add_done_callback(self._abort_on_error)

        if self._task.done() and self._queue.is_empty:
            return None

        return await self._queue.get_next()

    def _abort_on_error(self, task: Task):
        """Unblock the queue if fetching the responses failed.

        Without this, an exception in the fetching task would leave the consumer
        waiting for a response that is never going to arrive.

        Parameters
        ----------
        task : Task
            The finished task that fetched the responses.
        """
        if task.cancelled():
            return

        if error := task.exception():
            self._queue.abort(error)

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

        try:
            _request = session.build_request(
                method=request.method,
                url=request.url,
                data=request.data,
                json=request.json,
                params=request.params,
                headers=request.headers,
                timeout=request.timeout or 30,
            )

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

    async def _afetch_responses_worker(
        self,
        session: AsyncClient,
        requests: Iterator[tuple[int, Request]],
    ):
        """Fetch responses until the shared iterator of requests is exhausted.

        Pulling from a shared iterator instead of scheduling one task per request keeps
        the number of pending tasks (and pre-built HTTP requests) bounded by the batch
        size, so the first response does not have to wait for all requests to be set up.

        Parameters
        ----------
        session : AsyncClient
            HTTP session to use.
        requests : Iterator[tuple[int, Request]]
            Shared iterator yielding the priority and the resource to request.
        """
        # pulling from the iterator is atomic, because there is no await in between
        for priority, request in requests:
            LOGGER.debug(f"Scheduling request with priority {priority}")

            response = await self._asend_request(session, request, priority)

            await self._queue.put(priority, response)

    async def _afetch_responses(self):
        """Fetch all responses concurrently."""
        # shared by all workers, so that at most batch_size requests are in flight
        requests = iter(enumerate(self.requests))

        # the default pool would cap concurrency at 100 connections (20 kept alive),
        # regardless of the batch size
        limits = Limits(
            max_connections=self.batch_size,
            max_keepalive_connections=self.batch_size,
        )

        async with (
            AsyncClient(follow_redirects=True, http2=True, limits=limits) as session,
            TaskGroup() as tg,
        ):
            for _ in range(min(self.batch_size, self.num_requests)):
                tg.create_task(self._afetch_responses_worker(session, requests))
