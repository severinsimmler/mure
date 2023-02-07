from typing import Iterable

from mure.dtos import HTTPMethod, HTTPResource, Resource
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
    return _request("GET", resources, batch_size=batch_size)


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
    return _request("POST", resources, batch_size=batch_size)


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
    return _request("PUT", resources, batch_size=batch_size)


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
    return _request("PATCH", resources, batch_size=batch_size)


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
    return _request("DELETE", resources, batch_size=batch_size)


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
    return _request("HEAD", resources, batch_size=batch_size)


def _request(method: HTTPMethod, resources: Iterable[Resource], *, batch_size: int = 5) -> ResponseIterator:
    """Perform HTTP request using the specified method for each resource in the given batch.

    Note
    ----
    Only for internal use; preserves the type of the iterable (i.e. generator stays a generator).

    Parameters
    ----------
    method : HTTPMethod
        HTTP method to use.
    resources : Iterable[HTTPResource]
        Resources to request.
    batch_size : int
        Number of resources to request in parallel, by default 5.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    if isinstance(resources, list):
        return request([{**resource, "method": method} for resource in resources], batch_size=batch_size)
    else:
        return request(({**resource, "method": method} for resource in resources), batch_size=batch_size)
