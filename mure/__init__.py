from typing import Iterable

from mure.dtos import HTTPResource, Resource
from mure.iterator import ResponseIterator


def request(resources: Iterable[HTTPResource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[HTTPResource]
        Resources to request.
    batch_size : int
        Number of resources to request in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(resources, batch_size=batch_size)


def get(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform GET HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of resources to request in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return request([{"url": r["url"], "method": "GET"} for r in resources], batch_size=batch_size)


def post(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform GET HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return request([{"url": r["url"], "method": "POST"} for r in resources], batch_size=batch_size)


def put(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform PUT HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return request([{"url": r["url"], "method": "PUT"} for r in resources], batch_size=batch_size)


def patch(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform PATCH HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return request([{"url": r["url"], "method": "PATCH"} for r in resources], batch_size=batch_size)


def delete(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform DELETE HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return request([{"url": r["url"], "method": "DELETE"} for r in resources], batch_size=batch_size)


def head(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform HEAD HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return request([{"url": r["url"], "method": "HEAD"} for r in resources], batch_size=batch_size)
