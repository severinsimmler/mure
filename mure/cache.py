import json
import sqlite3
from abc import ABC, abstractmethod
from os import PathLike

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
        """Get a resource from the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to get from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the resource is not in the cache.
        """

    @abstractmethod
    def save(self, resource: HTTPResource, response: Response):
        """Save a resource to the cache.

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
        return json.dumps(
            {
                "method": resource["method"],
                "url": resource["url"],
                "headers": resource.get("headers"),
                "params": resource.get("params"),
                "data": resource.get("data"),
                "json": resource.get("json"),
            },
            sort_keys=True,
            ensure_ascii=False,
        )


class InMemoryCache(Cache):
    """Simple in-memory cache implementation."""

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
        """Get a resource from the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to get from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the resource is not in the cache.
        """
        return self._cache.get(self.identify_resource(resource))

    def save(self, resource: HTTPResource, response: Response):
        """Save a resource to the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to save to the cache.
        """
        self._cache[self.identify_resource(resource)] = response


class SQLiteCache(Cache):
    """SQLite cache implementation."""

    def __init__(self, path: PathLike):
        self.path = path
        self.db = sqlite3.connect(self.path)

        self.db.execute(
            """
                CREATE TABLE IF NOT EXISTS cache (
                    resource TEXT PRIMARY KEY,
                    response TEXT NOT NULL
                )
                """
        )

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
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT 1 FROM cache WHERE resource = ?;",
            (self.identify_resource(resource),),
        )
        return cursor.fetchone() is not None

    def get(self, resource: HTTPResource) -> Response | None:
        """Get a resource from the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to get from the cache.

        Returns
        -------
        Response | None
            Response from the cache or None if the resource is not in the cache.
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT response FROM cache WHERE resource = ?;",
            (self.identify_resource(resource),),
        )
        row = cursor.fetchone()
        return Response(**json.loads(row[0])) if row else None

    def save(self, resource: HTTPResource, response: Response):
        """Save a resource to the cache.

        Parameters
        ----------
        resource : HTTPResource
            Resource to save to the cache.
        """
        self.db.execute(
            "INSERT OR REPLACE INTO cache (resource, response) VALUES (?, ?);",
            (self.identify_resource(resource), json.dumps(response.__dict__)),
        )
