from asyncio import Lock
from pathlib import Path

import orjson

from mure.models import Request, Response


class ResponseStorage:
    """Storage for HTTP responses."""

    def __init__(self):
        """Initialize storage."""
        try:
            from databank import AsyncDatabase
            from databank.query import QueryCollection
        except ImportError as error:
            raise ImportError("Install mure with the `caching` extra dependencies") from error

        self.filepath = Path(".mure-cache.sqlite").resolve()
        self.exists = self.filepath.exists()

        self._db = AsyncDatabase(f"sqlite+aiosqlite:///{self.filepath}")
        self._queries = QueryCollection.from_file(Path(__file__).parent / "queries.sql")
        self._lock = Lock()

    async def asetup(self):
        """Set up the table for the storage."""
        async with self._lock:
            await self._db.aexecute(self._queries["create_table"])

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

    async def aclose(self):
        """Close the database connection."""
        await self._db.aclose()
