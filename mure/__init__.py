from typing import Iterable

from mure.dtos import HTTPMethod, HTTPResource, Resource
from mure.iterator import ResponseIterator


def request(
    resources: Iterable[HTTPResource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[HTTPResource]
        Resources to request.
    batch_size : int
        Number of resources to request in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(resources, batch_size=batch_size, log_errors=log_errors)


def get(
    resources: Iterable[Resource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform GET HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of resources to request in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return _request("GET", resources, batch_size=batch_size, log_errors=log_errors)


def post(
    resources: Iterable[Resource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform GET HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return _request("POST", resources, batch_size=batch_size, log_errors=log_errors)


def put(
    resources: Iterable[Resource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform PUT HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return _request("PUT", resources, batch_size=batch_size, log_errors=log_errors)


def patch(
    resources: Iterable[Resource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform PATCH HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return _request("PATCH", resources, batch_size=batch_size, log_errors=log_errors)


def delete(
    resources: Iterable[Resource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform DELETE HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return _request("DELETE", resources, batch_size=batch_size, log_errors=log_errors)


def head(
    resources: Iterable[Resource], *, batch_size: int = 5, log_errors: bool = True
) -> ResponseIterator:
    """Perform HEAD HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : Iterable[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch in parallel, by default 5.
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return _request("HEAD", resources, batch_size=batch_size, log_errors=log_errors)


def _request(
    method: HTTPMethod,
    resources: Iterable[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True
) -> ResponseIterator:
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
    log_errors : bool, optional
        True if Python errors should be logged, by default True.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    if isinstance(resources, list):
        return request(
            [{**resource, "method": method} for resource in resources],
            batch_size=batch_size,
            log_errors=log_errors,
        )
    else:
        return request(
            ({**resource, "method": method} for resource in resources),
            batch_size=batch_size,
            log_errors=log_errors,
        )
