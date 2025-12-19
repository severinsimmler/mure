from enum import Enum

from mure.cache.storage import FileStorage, MemoryStorage, SQLiteStorage, Storage


class Cache(Enum):
    """Enum for cache types."""

    SQLITE = "SQLITE"
    FILE = "FILE"
    MEMORY = "MEMORY"


def get_storage(cache: Cache | None) -> Storage | None:
    """Get the storage backend.

    Returns
    -------
    Storage
        Storage backend.
    """
    match cache:
        case Cache.SQLITE:
            return SQLiteStorage()
        case Cache.FILE:
            return FileStorage()
        case Cache.MEMORY:
            return MemoryStorage()
        case _:
            return None
