import asyncio
import contextlib
from asyncio import CancelledError
from collections.abc import Generator
from queue import SimpleQueue
from threading import Event, Thread

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
    queue: SimpleQueue[Response | BaseException | None] = SimpleQueue()

    # set as soon as the event loop and its main task are known
    started = Event()
    context: dict = {}

    async def main():
        context["loop"] = asyncio.get_running_loop()
        context["task"] = asyncio.current_task()
        started.set()

        try:
            async with AsyncResponseIterator(
                requests,
                batch_size=batch_size,
                cache=cache,
            ) as responses:
                async for response in responses:
                    queue.put(response)
        except CancelledError:
            # the generator was closed before all responses were consumed
            pass
        except BaseException as error:
            # re-raise in the consuming thread instead of blocking it forever
            queue.put(error)
        finally:
            # signal that we're done
            queue.put(None)

    def run_main():
        asyncio.run(main())

    # run the async main function in a separate thread; it is a daemon so that a
    # crashed or wedged event loop can never keep the interpreter alive
    thread = Thread(target=run_main, daemon=True)
    thread.start()

    is_finished = False
    try:
        while True:
            response = queue.get()

            # no more responses to fetch
            if response is None:
                is_finished = True
                break

            if isinstance(response, BaseException):
                raise response

            yield response
    finally:
        # the consumer may abandon the generator early (e.g. by breaking out of the
        # loop), in which case the remaining requests must not be fired anymore
        if started.wait(timeout=5):
            # RuntimeError is raised if the generator is only collected at interpreter shutdown;
            # the thread is a daemon, so leaving it running is fine in that case
            with contextlib.suppress(RuntimeError):
                if not is_finished:
                    # cancelling once everything has been fetched would interrupt the
                    # clean shutdown (e.g. closing the cache's database connection)
                    context["loop"].call_soon_threadsafe(context["task"].cancel)

                thread.join()
