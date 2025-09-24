from json import JSONDecodeError

import pytest

import mure
from mure.models import Resource, Response


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
    assert responses[0].ok
    assert responses[1].ok
    assert not responses[2].ok


def test_json():
    response = next(mure.get([{"url": "https://httpbin.org/get"}]))

    assert len(response.json()) == 4


def test_invalid_json():
    with pytest.raises(JSONDecodeError):
        next(mure.get([{"url": "https://wikipedia.org"}])).json()
