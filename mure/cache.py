from enum import StrEnum

from hishel import AsyncBaseStorage, AsyncSqliteStorage


class Cache(StrEnum):
    """Available cache backends."""

    SQLITE = "SQLITE"


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
        case Cache.SQLITE:
            return AsyncSqliteStorage()
        case _:
            raise ValueError(f"Unsupported cache type: {cache}")
