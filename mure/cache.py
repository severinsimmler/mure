import shelve
from abc import ABC, abstractmethod
from pathlib import Path

from mure.logging import Logger
from mure.models import Request, Response

LOGGER = Logger(__name__)


class Cache(ABC):
    """Abstract class for a cache to store responses."""

    @abstractmethod
    def has(self, request: Request) -> bool:
        """Check if a request (and its corresponding response) is in the cache.

        Parameters
        ----------
        request : Request
            Request to check if it's in the cache.

        Returns
        -------
        bool
            True if the request is in the cache; otherwise, False.
        """

    @abstractmethod
    def get(self, request: Request) -> Response | None:
        """Get the response for the specified request from the cache.

        Parameters
        ----------
        request : Request
            Request to get response from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the request is not in the cache.
        """

    @abstractmethod
    def set(self, request: Request, response: Response):
        """Save a request and its response to the cache.

        Parameters
        ----------
        request : Request
            Request to save to the cache.
        response : Response
            Response to save to the cache.
        """


class MemoryCache(Cache):
    """Simple in-memory cache."""

    def __init__(self):
        self._cache = {}

    def has(self, request: Request) -> bool:
        """Check if a request (and its corresponding response) is in the cache.

        Parameters
        ----------
        request : Request
            Request to check if it's in the cache.

        Returns
        -------
        bool
            True if the request is in the cache; otherwise, False.
        """
        return request.id in self._cache

    def get(self, request: Request) -> Response | None:
        """Get the response for the specified request from the cache.

        Parameters
        ----------
        request : Request
            Request to get response from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the request is not in the cache.
        """
        return self._cache.get(request.id)

    def set(self, request: Request, response: Response):
        """Save a request and its response to the cache.

        Parameters
        ----------
        request : Request
            Request to save to the cache.
        response : Response
            Response to save to the cache.
        """
        self._cache[request.id] = response


class DiskCache(MemoryCache):
    """Simple on-disk cache."""

    def __init__(self, path: Path = Path("mure-cache.shelve")):
        super().__init__()

        self.path = path.resolve()
        if self.path.exists():
            LOGGER.warning(f"Cache ({self.path}) already exists")

        self._cache = shelve.open(str(self.path))

    def __del__(self):
        """Close the cache."""
        self._cache.close()
