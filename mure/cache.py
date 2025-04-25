from enum import StrEnum

from hishel import (
    HEURISTICALLY_CACHEABLE_STATUS_CODES,
    AsyncBaseStorage,
    AsyncFileStorage,
    AsyncInMemoryStorage,
    AsyncSQLiteStorage,
    Controller,
)


class Cache(StrEnum):
    """Available cache backends."""

    FILE = "FILE"
    IN_MEMORY = "IN_MEMORY"
    SQLITE = "SQLITE"


class CacheController(Controller):
    """Cache controller for HTTP requests."""

    def __init__(self):
        super().__init__(
            cacheable_methods=["GET", "POST"],
            force_cache=True,
            allow_heuristics=True,
            cacheable_status_codes=[*HEURISTICALLY_CACHEABLE_STATUS_CODES, 0, 500],
        )


def get_storage(cache: Cache) -> AsyncBaseStorage:
    """Get storage backend based on the cache type.

    Parameters
    ----------
    cache : Cache
        Cache type.

    Returns
    -------
    AsyncBaseStorage
        Storage backend.
    """
    match cache:
        case Cache.FILE:
            return AsyncFileStorage()
        case Cache.IN_MEMORY:
            return AsyncInMemoryStorage()
        case Cache.SQLITE:
            return AsyncSQLiteStorage()
