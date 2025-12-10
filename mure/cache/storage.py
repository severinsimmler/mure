import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mure.models import Request, Response


class Storage:
    """Storage for HTTP responses."""

    def __init__(self) -> None:
        """Initialize storage.

        Parameters
        ----------
        storage : AsyncBaseStorage
            Storage backend.
        """
        try:
            from databank import AsyncDatabase
            from databank.query import QueryCollection
        except ImportError as error:
            raise ImportError("Install mure with the `caching` extra dependencies") from error

        self.filepath = Path(".mure-cache.sqlite").resolve()
        self.exists = self.filepath.exists()

        self._db = AsyncDatabase(f"sqlite+aiosqlite:///{self.filepath}")
        self._queries = QueryCollection.from_file(Path(__file__).parent / "queries.sql")

    async def asetup(self):
        """Set up the table for the storage."""
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

        await self._db.aexecute(
            self._queries["save_response"],
            params={
                "key": hash_request(request),
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
        if record := await self._db.afetch_one(
            self._queries["get_response"],
            params={"key": hash_request(request)},
        ):
            return Response(
                ok=bool(record["ok"]),
                status=record["status"],
                reason=record["reason"],
                url=record["url"],
                content=record["content"],
                encoding=record["encoding"],
                headers=json.loads(record["headers"]),
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
        "method": request.method.upper(),
        "url": request.url.lower(),
        "headers": _normalize(request.headers),
        "params": _normalize(request.params),
        "data": _normalize(request.data),
        "json": _normalize(request.json),
    }

    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


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
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return repr(value)
