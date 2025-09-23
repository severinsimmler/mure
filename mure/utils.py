import asyncio

from mure.cache import Cache
from mure.iterator import AsyncResponseIterator
from mure.models import Request


def fetch_responses(requests: list[Request], *, batch_size: int = 5, cache: Cache | None = None):
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

    async def _agenerator_wrapper():
        async with AsyncResponseIterator(requests, batch_size=batch_size, cache=cache) as iterator:
            async for response in iterator:
                yield response

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        agenerator = _agenerator_wrapper()

        while True:
            try:
                yield loop.run_until_complete(anext(agenerator))
            except StopAsyncIteration:
                break
    finally:
        loop.close()
        asyncio.set_event_loop(None)
