from typing import Iterable

from mure.dtos import Resource
from mure.utils import ResponseIterator


def request(resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform HTTP request for each resource in the given batch.

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
    return request([r | {"method": "GET"} for r in resources], batch_size=batch_size)


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
    return request([r | {"method": "POST"} for r in resources], batch_size=batch_size)


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
    return request([r | {"method": "PUT"} for r in resources], batch_size=batch_size)


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
    return request([r | {"method": "PATCH"} for r in resources], batch_size=batch_size)


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
    return request([r | {"method": "DELETE"} for r in resources], batch_size=batch_size)
