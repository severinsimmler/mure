import asyncio
from collections.abc import Generator

from mure.cache import Cache
from mure.iterator import AsyncResponseIterator
from mure.models import Request, Response


def fetch_responses(
    requests: list[Request],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Fetch responses for a list of requests.

    Parameters
    ----------
    requests : list[Request]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Yields
    ------
    Response
        The server's response for each request.
    """
    if asyncio.events._get_running_loop() is not None:
        raise RuntimeError("This function cannot be called from a running event loop")

    responses = AsyncResponseIterator(requests, batch_size=batch_size, cache=cache)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        for _ in requests:
            response = loop.run_until_complete(responses.aconsume_next_response())

            if response is None:
                raise ValueError("There are inconsistencies between requests and responses")

            yield response
    finally:
        loop.run_until_complete(responses.aclose())
        loop.close()
        asyncio.set_event_loop(None)
