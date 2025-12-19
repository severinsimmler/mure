import importlib.util
from abc import ABC, abstractmethod
from asyncio import Lock
from pathlib import Path

import orjson

from mure.models import Request, Response


class Storage(ABC):
    """Abstract storage class."""

    @abstractmethod
    async def asetup(self):
        """Set up the the storage."""

    @abstractmethod
    async def acleanup(self):
        """Clean up the storage."""

    @property
    @abstractmethod
    def exists(self) -> bool:
        """Check if the storage exists.

        Returns
        -------
        bool
            Whether the storage exists.
        """

    @abstractmethod
    async def asave_response(self, request: Request, response: Response):
        """Save a response to the storage.

        Parameters
        ----------
        request : Request
            Resource requested.
        response : Response
            Response to save.
        """

    @abstractmethod
    async def aget_response(self, request: Request) -> Response | None:
        """Get a cached response for a request.

        Parameters
        ----------
        request : Request
            Resource to request.

        Returns
        -------
        Response | None
            Cached response, or None if not found.
        """


class SQLiteStorage(Storage):
    """SQLite storage for HTTP responses."""

    def __init__(self):
        """Initialize storage."""
        if not importlib.util.find_spec("databank"):
            raise ImportError("Install mure with the `sqlite` extra dependencies")

        from databank import AsyncDatabase
        from databank.query import QueryCollection

        self.filepath = Path.cwd() / ".mure-cache.sqlite"

        self._db = AsyncDatabase(f"sqlite+aiosqlite:///{self.filepath}")
        self._queries = QueryCollection.from_file(Path(__file__).parent / "queries.sql")
        self._lock = Lock()

    @property
    def exists(self) -> bool:
        """Check if the storage exists.

        Returns
        -------
        bool
            Whether the storage exists.
        """
        return self.filepath.exists()

    async def asetup(self):
        """Set up the table for the storage."""
        async with self._lock:
            await self._db.aexecute(self._queries["create_table"])

    async def acleanup(self):
        """Close the database connection."""
        async with self._lock:
            await self._db.aclose()

    async def asave_response(self, request: Request, response: Response):
        """Save a response to the cache.

        Parameters
        ----------
        request : Request
            Resource requested.
        response : Response
            Response to save.
        """
        async with self._lock:
            await self._db.aexecute(
                self._queries["save_response"],
                params={
                    "key": request.sha256(),
                    "url": response.url,
                    "headers": orjson.dumps(response.headers).decode("utf-8"),
                    "status": response.status,
                    "ok": response.ok,
                    "reason": response.reason,
                    "content": response.content,
                    "encoding": response.encoding,
                },
            )

    async def aget_response(self, request: Request) -> Response | None:
        """Get a cached response for a request.

        Parameters
        ----------
        request : Request
            Resource to request.

        Returns
        -------
        Response | None
            Cached response, or None if not found.
        """
        async with self._lock:
            if record := await self._db.afetch_one(
                self._queries["get_response"],
                params={"key": request.sha256()},
            ):
                return Response(
                    ok=bool(record["ok"]),
                    status=record["status"],
                    reason=record["reason"],
                    url=record["url"],
                    content=record["content"],
                    encoding=record["encoding"],
                    headers=orjson.loads(record["headers"]),
                )

        return None


class MemoryStorage(Storage):
    """Memory storage for HTTP responses."""

    def __init__(self):
        """Initialize storage."""
        self._memory: dict[str, Response] = {}
        self._lock = Lock()

    @property
    def exists(self) -> bool:
        """Check if the storage exists.

        Returns
        -------
        bool
            Whether the storage exists.
        """
        return True

    async def asetup(self):
        """Nothing to set up."""

    async def acleanup(self):
        """Nothing to clean up."""

    async def asave_response(self, request: Request, response: Response):
        """Save a response to the cache.

        Parameters
        ----------
        request : Request
            Resource requested.
        response : Response
            Response to save.
        """
        async with self._lock:
            self._memory[request.sha256()] = response

    async def aget_response(self, request: Request) -> Response | None:
        """Get a cached response for a request.

        Parameters
        ----------
        request : Request
            Resource to request.

        Returns
        -------
        Response | None
            Cached response, or None if not found.
        """
        async with self._lock:
            return self._memory.get(request.sha256(), None)


class FileStorage(Storage):
    """File storage for HTTP responses."""

    def __init__(self):
        """Initialize storage.

        Parameters
        ----------
        directory : Path
            Directory to store cached responses.
        """
        if not importlib.util.find_spec("msgpack"):
            raise ImportError("Install mure with the `msgpack` extra dependencies")

        self.directory = Path.cwd() / ".mure-cache"
        self._lock = Lock()

    @property
    def exists(self) -> bool:
        """Check if the storage exists.

        Returns
        -------
        bool
            Whether the storage exists.
        """
        return self.directory.exists()

    async def asetup(self):
        """Set up the file storage."""
        self.directory.mkdir(parents=True, exist_ok=True)

    async def acleanup(self):
        """Nothing to clean up."""

    async def asave_response(self, request: Request, response: Response):
        """Save a response to the cache.

        Parameters
        ----------
        request : Request
            Resource requested.
        response : Response
            Response to save.
        """
        import msgpack

        async with self._lock:
            filepath = self.directory / f"{request.sha256()}.msgpack"
            with filepath.open("wb") as f:
                msgpack.dump(
                    {
                        "url": response.url,
                        "headers": response.headers,
                        "status": response.status,
                        "ok": response.ok,
                        "reason": response.reason,
                        "content": response.content,
                        "encoding": response.encoding,
                    },
                    f,
                )

    async def aget_response(self, request: Request) -> Response | None:
        """Get a cached response for a request.

        Parameters
        ----------
        request : Request
            Resource to request.

        Returns
        -------
        Response | None
            Cached response, or None if not found.
        """
        import msgpack

        async with self._lock:
            filepath = self.directory / f"{request.sha256()}.msgpack"
            if not filepath.exists():
                return None

            with filepath.open("rb") as f:
                data = msgpack.load(f)
                return Response(
                    ok=bool(data["ok"]),  # type: ignore
                    status=data["status"],  # type: ignore
                    reason=data["reason"],  # type: ignore
                    url=data["url"],  # type: ignore
                    content=data["content"],  # type: ignore
                    encoding=data["encoding"],  # type: ignore
                    headers=data["headers"],  # type: ignore
                )
