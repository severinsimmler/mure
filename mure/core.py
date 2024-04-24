from mure.cache import Cache
from mure.iterator import ResponseIterator
from mure.models import Request, Resource


def delete(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> ResponseIterator:
    """Perform a DELETE request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(
        [Request("DELETE", **resource) for resource in resources],
        batch_size=batch_size,
        cache=cache,
    )


def get(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> ResponseIterator:
    """Perform a GET request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(
        [Request("GET", **resource) for resource in resources],
        batch_size=batch_size,
        cache=cache,
    )


def head(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> ResponseIterator:
    """Perform a HEAD request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(
        [Request("HEAD", **resource) for resource in resources],
        batch_size=batch_size,
        cache=cache,
    )


def patch(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> ResponseIterator:
    """Perform a PATCH request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(
        [Request("PATCH", **resource) for resource in resources],
        batch_size=batch_size,
        cache=cache,
    )


def post(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> ResponseIterator:
    """Perform a POST request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(
        [Request("POST", **resource) for resource in resources],
        batch_size=batch_size,
        cache=cache,
    )


def put(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> ResponseIterator:
    """Perform a PUT request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Cache to use for storing responses, by default None.

    Returns
    -------
    ResponseIterator
        The server's responses for each resource.
    """
    return ResponseIterator(
        [Request("PUT", **resource) for resource in resources],
        batch_size=batch_size,
        cache=cache,
    )
