import asyncio
from collections.abc import Generator
from queue import SimpleQueue
from threading import Thread

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
        Which kind of cache to use, by default None.

    Yields
    ------
    Response
        The server's response for each request.
    """
    # queue to communicate between the async thread and the generator
    queue: SimpleQueue[Response | None] = SimpleQueue()

    async def main():
        async for response in AsyncResponseIterator(requests, batch_size=batch_size, cache=cache):
            queue.put(response)

        # signal that we're done
        queue.put(None)

    def run_main():
        asyncio.run(main())

    # run the async main function in a separate thread
    thread = Thread(target=run_main)
    thread.start()

    while True:
        response = queue.get()

        # no more responses to fetch
        if response is None:
            break

        yield response
