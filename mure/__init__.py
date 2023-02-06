import asyncio
from typing import Iterable, Iterator

from aiohttp import ClientSession

from mure.dtos import Resource, Response
from mure.logging import Logger
from mure.utils import chunk

LOGGER = Logger(__name__)


def request(resources: Iterable[Resource], *, batch_size: int = 5) -> Iterator[Response]:
    """Perform HTTP request for each resource in the given batch.

    Parameters
    ----------
    resource : Resource
        Resource to request.
    batch_size : int
        Number of items to request in parallel, by default 5.

    Returns
    -------
    Iterator[Response]
        The server's responses for each resource.
    """
    for batch in chunk(resources, n=batch_size):
        yield from asyncio.run(_process_batch(batch))


def get(resources: Iterable[Resource], *, batch_size: int = 5) -> Iterator[Response]:
    """Perform GET HTTP request for each resource in the given batch.

    Parameters
    ----------
    resource : Resource
        Resource to request.
    batch_size : int
        Number of items to request in parallel, by default 5.

    Returns
    -------
    Iterator[Response]
        The server's responses for each resource.
    """
    yield from request([r | {"method": "GET"} for r in resources], batch_size=batch_size)


def post(resources: Iterable[Resource], *, batch_size: int = 5) -> Iterator[Response]:
    """Perform GET HTTP request for each resource in the given batch.

    Parameters
    ----------
    resource : Resource
        Resource to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.

    Returns
    -------
    Iterator[Response]
        The server's responses for each resource.
    """
    yield from request([r | {"method": "POST"} for r in resources], batch_size=batch_size)


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


async def _process_batch(resources: Iterable[Resource]) -> list[Response]:
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
        requests = [_process(session, resource) for resource in resources]
        return await asyncio.gather(*requests)
