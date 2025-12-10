import hashlib
from asyncio import Lock
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

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
        from databank.utils import serialize_param

        key = hash_request(request)

        async with self._lock:
            await self._db.aexecute(
                self._queries["save_response"],
                params={
                    "key": key,
                    "url": response.url,
                    "headers": serialize_param(dict(response.headers)),
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
        key = hash_request(request)

        async with self._lock:
            if record := await self._db.afetch_one(
                self._queries["get_response"],
                params={"key": key},
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


def hash_request(request: Request) -> str:
    """Create a hash for a request.

    Parameters
    ----------
    request : Request
        Request to hash.

    Returns
    -------
    str
        Hash of the request.
    """
    data = {
        "method": request.method.upper().strip(),
        "url": request.url.lower().strip(),
        "headers": _normalize({k.lower().strip(): v for k, v in request.headers.items()})
        if request.headers
        else None,
        "params": _normalize(request.params),
        "data": _normalize(request.data),
        "json": _normalize(request.json),
    }

    return hashlib.sha256(orjson.dumps(data, option=orjson.OPT_SORT_KEYS)).hexdigest()


def _sort_key(item: tuple[Any, Any]) -> str:
    """Sort key for normalizing mappings."""
    return str(item[0])


def _normalize(value: Any) -> Any:
    """Normalize a value for hashing."""
    if value is None:
        return None

    if isinstance(value, bytes):
        return {"__type": "bytes", "sha256": hashlib.sha256(value).hexdigest()}

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in sorted(value.items(), key=_sort_key)}

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize(v) for v in value]

    try:
        return orjson.dumps(value, option=orjson.OPT_SORT_KEYS).decode("utf-8")
    except TypeError:
        return repr(value)
