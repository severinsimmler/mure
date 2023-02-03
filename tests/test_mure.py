import pytest

import mure


def test_get():
    resources = [
        {"url": "https://httpbin.org/get"},
        {"url": "https://httpbin.org/get", "params": {"foo": "bar"}},
        {"url": "invalid"},
    ]

    responses = list(mure.get(resources, batch_size=2))

    assert len(responses) == 3
    assert responses[0]["ok"]
    assert responses[1]["ok"]
    assert not responses[2]["ok"]


def test_post():
    resources = [
        {"url": "https://httpbin.org/post"},
        {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
        {"url": "invalid"},
    ]

    responses = list(mure.post(resources, batch_size=2))

    assert len(responses) == 3
    assert responses[0]["ok"]
    assert responses[1]["ok"]
    assert not responses[2]["ok"]


def test_mixed():
    resources = [
        {"method": "GET", "url": "https://httpbin.org/get"},
        {"method": "GET", "url": "https://httpbin.org/get", "params": {"foo": "bar"}},
        {"method": "POST", "url": "https://httpbin.org/post"},
        {"method": "POST", "url": "https://httpbin.org/post", "json": {"foo": "bar"}},
        {"method": "GET", "url": "invalid"},
    ]

    responses = list(mure.request(resources, batch_size=2))

    assert len(responses) == 5
    assert responses[0]["ok"]
    assert responses[1]["ok"]
    assert responses[2]["ok"]
    assert responses[3]["ok"]
    assert not responses[4]["ok"]


def test_missing_method():
    with pytest.raises(KeyError):
        list(mure.request([{"url": "https://httpbin.org/get"}]))
