import json
import shelve
from abc import ABC, abstractmethod
from hashlib import blake2b
from pathlib import Path

from mure.dtos import HTTPResource, Response


class Cache(ABC):
    """Abstract class for a cache."""

    @abstractmethod
    def has(self, resource: HTTPResource) -> bool:
        """Check if a resource is in the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to check if it's in the cache.

        Returns
        -------
        bool
            True if the resource is in the cache; otherwise, False.
        """

    @abstractmethod
    def get(self, resource: HTTPResource) -> Response | None:
        """Get the response for the specified resource from the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to get response from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the resource is not in the cache.
        """

    @abstractmethod
    def set(self, resource: HTTPResource, response: Response):
        """Save a resource and its response to the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to save to the cache.
        response : Response
            Response to save to the cache.
        """

    def identify_resource(self, resource: HTTPResource) -> str:
        """Identify a resource.

        Parameters
        ----------
        resource : HTTPResource
            Resource to get an identifier for.

        Returns
        -------
        str
            JSON representation of the resource.
        """
        # generate a hash based on the components
        key = blake2b(digest_size=8)
        for part in [
            resource["method"],
            resource["url"],
            json.dumps(resource.get("params"), sort_keys=True, ensure_ascii=False),
            json.dumps(resource.get("data"), sort_keys=True, ensure_ascii=False),
            json.dumps(resource.get("json"), sort_keys=True, ensure_ascii=False),
        ]:
            key.update(self._encode(part))

        return key.hexdigest()

    @staticmethod
    def _encode(value: str) -> bytes:
        """Encode a string to bytes.

        Parameters
        ----------
        value : str
            String to encode.

        Returns
        -------
        bytes
            Encoded string.
        """
        if not value:
            return b""

        return value if isinstance(value, bytes) else str(value).encode("utf-8")


class InMemoryCache(Cache):
    """Simple in-memory cache."""

    def __init__(self):
        self._cache = {}

    def has(self, resource: HTTPResource) -> bool:
        """Check if a resource is in the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to check if it's in the cache.

        Returns
        -------
        bool
            True if the resource is in the cache; otherwise, False.
        """
        return self.identify_resource(resource) in self._cache

    def get(self, resource: HTTPResource) -> Response | None:
        """Get the response for the specified resource from the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to get response from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the resource is not in the cache.
        """
        return self._cache.get(self.identify_resource(resource))

    def set(self, resource: HTTPResource, response: Response):
        """Save a resource and its response to the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to save to the cache.
        response : Response
            Response to save to the cache.
        """
        self._cache[self.identify_resource(resource)] = response


class ShelveCache(InMemoryCache):
    """Shelve cache."""

    def __init__(self, path: Path = Path("mure-cache.shelve")):
        super().__init__()

        self.path = path
        self._cache = shelve.open(str(self.path.resolve()))
