from collections.abc import Generator

from mure.models import Request, Resource, Response
from mure.utils import fetch_responses


def delete(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    enable_cache: bool = False,
) -> Generator[Response]:
    """Perform a DELETE request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    enable_cache : bool, optional
        Whether to use a cache for storing responses, by default False.

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
            enable_cache=enable_cache,
        )
    )


def get(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    enable_cache: bool = False,
) -> Generator[Response]:
    """Perform a GET request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    enable_cache : bool, optional
        Whether to use a cache for storing responses, by default False.

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
            enable_cache=enable_cache,
        )
    )


def head(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    enable_cache: bool = False,
) -> Generator[Response]:
    """Perform a HEAD request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    enable_cache : bool, optional
        Whether to use a cache for storing responses, by default False.

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
            enable_cache=enable_cache,
        )
    )


def patch(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    enable_cache: bool = False,
) -> Generator[Response]:
    """Perform a PATCH request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    enable_cache : bool, optional
        Whether to use a cache for storing responses, by default False.

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
            enable_cache=enable_cache,
        )
    )


def post(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    enable_cache: bool = False,
) -> Generator[Response]:
    """Perform a POST request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    enable_cache : bool, optional
        Whether to use a cache for storing responses, by default False.

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
            enable_cache=enable_cache,
        )
    )


def put(
    resources: list[Resource],
    *,
    batch_size: int = 5,
    enable_cache: bool = False,
) -> Generator[Response]:
    """Perform a PUT request for each resource.

    Parameters
    ----------
    resources : list[Resource]
        Resources to request.
    batch_size : int
        Number of items to request per batch concurrently, by default 5.
    enable_cache : bool, optional
        Whether to use a cache for storing responses, by default False.

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
            enable_cache=enable_cache,
        )
    )
