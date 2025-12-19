from collections.abc import Generator

from mure.cache import Cache
from mure.models import Request, Resource, Response
from mure.utils import fetch_responses


def delete(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Perform a DELETE request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Which kind of cache to use, by default None.

    Returns
    -------
    Generator[Response]
        The server's responses for each resource.
    """
    return (
        response
        for response in fetch_responses(
            [
                Request(
                    "DELETE",
                    resource["url"],
                    headers=resource.get("headers"),
                    params=resource.get("params"),
                    data=resource.get("data"),
                    json=resource.get("json"),
                    timeout=resource.get("timeout"),
                )
                for resource in resources
            ],
            batch_size=batch_size,
            cache=cache,
        )
    )


def get(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Perform a GET request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Which kind of cache to use, by default None.

    Returns
    -------
    Generator[Response]
        The server's responses for each resource.
    """
    return (
        response
        for response in fetch_responses(
            [
                Request(
                    "GET",
                    resource["url"],
                    headers=resource.get("headers"),
                    params=resource.get("params"),
                    data=resource.get("data"),
                    json=resource.get("json"),
                    timeout=resource.get("timeout"),
                )
                for resource in resources
            ],
            batch_size=batch_size,
            cache=cache,
        )
    )


def head(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Perform a HEAD request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Which kind of cache to use, by default None.

    Returns
    -------
    Generator[Response]
        The server's responses for each resource.
    """
    return (
        response
        for response in fetch_responses(
            [
                Request(
                    "HEAD",
                    resource["url"],
                    headers=resource.get("headers"),
                    params=resource.get("params"),
                    data=resource.get("data"),
                    json=resource.get("json"),
                    timeout=resource.get("timeout"),
                )
                for resource in resources
            ],
            batch_size=batch_size,
            cache=cache,
        )
    )


def patch(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Perform a PATCH request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Which kind of cache to use, by default None.

    Returns
    -------
    Generator[Response]
        The server's responses for each resource.
    """
    return (
        response
        for response in fetch_responses(
            [
                Request(
                    "PATCH",
                    resource["url"],
                    headers=resource.get("headers"),
                    params=resource.get("params"),
                    data=resource.get("data"),
                    json=resource.get("json"),
                    timeout=resource.get("timeout"),
                )
                for resource in resources
            ],
            batch_size=batch_size,
            cache=cache,
        )
    )


def post(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Perform a POST request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Which kind of cache to use, by default None.

    Returns
    -------
    Generator[Response]
        The server's responses for each resource.
    """
    return (
        response
        for response in fetch_responses(
            [
                Request(
                    "POST",
                    resource["url"],
                    headers=resource.get("headers"),
                    params=resource.get("params"),
                    data=resource.get("data"),
                    json=resource.get("json"),
                    timeout=resource.get("timeout"),
                )
                for resource in resources
            ],
            batch_size=batch_size,
            cache=cache,
        )
    )


def put(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    cache: Cache | None = None,
) -> Generator[Response]:
    """Perform a PUT request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    cache : Cache | None, optional
        Which kind of cache to use, by default None.

    Returns
    -------
    Generator[Response]
        The server's responses for each resource.
    """
    return (
        response
        for response in fetch_responses(
            [
                Request(
                    "PUT",
                    resource["url"],
                    headers=resource.get("headers"),
                    params=resource.get("params"),
                    data=resource.get("data"),
                    json=resource.get("json"),
                    timeout=resource.get("timeout"),
                )
                for resource in resources
            ],
            batch_size=batch_size,
            cache=cache,
        )
    )
