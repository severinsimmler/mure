from pathlib import Path

from mure.cache import DiskCache, MemoryCache
from mure.models import Request, Response


def test_memory_cache():
    cache = MemoryCache()
    request = Request("GET", "https://httpbin.org/get")
    response = Response(ok=True, status=200, reason="OK", url="https://httpbin.org/get", text="")

    assert not cache.has(request)
    assert cache.get(request) is None

    cache.set(request, response)

    assert cache.has(request)
    assert cache.get(request) == response


def test_disk_cache(tmp_path: Path):
    path = tmp_path / "mure-cache.shelve"

    assert not path.exists()
    cache = DiskCache(path)

    assert path.exists()
    request = Request("GET", "https://httpbin.org/get")
    response = Response(ok=True, status=200, reason="OK", url="https://httpbin.org/get", text="")

    assert not cache.has(request)
    assert cache.get(request) is None

    cache.set(request, response)

    assert cache.has(request)
    assert cache.get(request) is not None

    # may not be empty
    assert path.stat().st_size > 0
