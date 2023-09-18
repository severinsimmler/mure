from mure.dtos import DELETE, GET, HEAD, PATCH, POST, PUT, HTTPMethod, HTTPResource, Resource
from mure.iterator import ResponseIterator


def request(
    resources: list[HTTPResource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform HTTP request for each resource in the given batch.

    Parameters
    ----------
    resources : list[HTTPResource]
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
    if not isinstance(resources, list):
        raise TypeError(f"Expected list of resources, got {type(resources)}")

    if any("method" not in resource for resource in resources):
        raise KeyError("Missing HTTP method in resource")

    if any("url" not in resource for resource in resources):
        raise KeyError("Missing URL in resource")

    return ResponseIterator(resources, batch_size=batch_size, log_errors=log_errors)


def get(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a GET request for each resource.

    Parameters
    ----------
    resources : list[Resource]
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
    return _request(GET, resources, batch_size=batch_size, log_errors=log_errors)


def post(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a POST request for each resource.

    Parameters
    ----------
    resources : list[Resource]
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
    return _request(POST, resources, batch_size=batch_size, log_errors=log_errors)


def put(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a PUT request for each resource.

    Parameters
    ----------
    resources : list[Resource]
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
    return _request(PUT, resources, batch_size=batch_size, log_errors=log_errors)


def patch(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a PATCH request for each resource.

    Parameters
    ----------
    resources : list[Resource]
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
    return _request(PATCH, resources, batch_size=batch_size, log_errors=log_errors)


def delete(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a DELETE request for each resource.

    Parameters
    ----------
    resources : list[Resource]
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
    return _request(DELETE, resources, batch_size=batch_size, log_errors=log_errors)


def head(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a HEAD request for each resource.

    Parameters
    ----------
    resources : list[Resource]
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
    return _request(HEAD, resources, batch_size=batch_size, log_errors=log_errors)


def _request(
    method: HTTPMethod,
    resources: list[Resource],
    *,
    batch_size: int = 5,
    log_errors: bool = True,
) -> ResponseIterator:
    """Perform a HTTP request using the specified method for each resource.

    Parameters
    ----------
    method : HTTPMethod
        HTTP method to use.
    resources : list[HTTPResource]
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
    return request(
        [{**resource, "method": method} for resource in resources],
        batch_size=batch_size,
        log_errors=log_errors,
    )
