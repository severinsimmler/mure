from json import JSONDecodeError
from unittest.mock import patch

import pytest

import mure
from mure.cache import InMemoryCache
from mure.dtos import HTTPResource, Resource, Response


def test_get():
    resources: list[Resource] = [
        {"url": "https://httpbin.org/get"},
        {"url": "https://httpbin.org/get", "params": {"foo": "bar"}},
        {"url": "invalid"},
    ]

    responses: list[Response] = list(mure.get(resources, batch_size=2))

    assert len(responses) == 3
    assert responses[0].ok
    assert responses[1].ok
    assert not responses[2].ok


def test_post():
    resources: list[Resource] = [
        {"url": "https://httpbin.org/post"},
        {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
        {"url": "invalid"},
    ]

    responses: list[Response] = list(mure.post(resources, batch_size=2))

    assert len(responses) == 3
    assert responses[0]["ok"]
    assert responses[1]["ok"]
    assert not responses[2]["ok"]


def test_mixed():
    resources: list[HTTPResource] = [
        {"method": "GET", "url": "https://httpbin.org/get"},
        {"method": "GET", "url": "https://httpbin.org/get", "params": {"foo": "bar"}},
        {"method": "POST", "url": "https://httpbin.org/post"},
        {"method": "POST", "url": "https://httpbin.org/post", "json": {"foo": "bar"}},
        {"method": "GET", "url": "invalid"},
    ]

    responses: list[Response] = list(mure.request(resources, batch_size=2))

    assert len(responses) == 5
    assert responses[0]["ok"]
    assert responses[1]["ok"]
    assert responses[2]["ok"]
    assert responses[3]["ok"]
    assert not responses[4]["ok"]


def test_missing_method():
    with pytest.raises(KeyError):
        next(mure.request([{"url": "https://httpbin.org/get"}]))


def test_json():
    response = next(mure.get([{"url": "https://httpbin.org/get"}]))

    assert len(response.json()) == 4


def test_invalid_json():
    with pytest.raises(JSONDecodeError):
        next(mure.get([{"url": "https://wikipedia.org"}])).json()


def test_cache(monkeypatch: pytest.MonkeyPatch):
    cache = InMemoryCache()
    resource: HTTPResource = {"method": "GET", "url": "https://httpbin.org/get"}

    # resource is not in the cache
    assert not cache.has(resource)

    with (
        patch("mure.iterator.ResponseIterator.cache.get") as get,
        patch("mure.iterator.ResponseIterator.cache.save") as save,
    ):
        next(mure.get([resource], cache=cache))
        get.assert_called_once()
        save.assert_called_once()

    # resource is now in the cache
    assert cache.has(resource)

    with (
        patch("mure.iterator.ResponseIterator.cache.get") as get,
        patch("mure.iterator.ResponseIterator.cache.save") as save,
    ):
        next(mure.get([resource], cache=cache))
        get.assert_called_once()
        save.assert_not_called()
