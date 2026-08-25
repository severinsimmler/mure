# mure

[![downloads](https://static.pepy.tech/personalized-badge/mure?period=total&units=international_system&left_color=black&right_color=black&left_text=downloads)](https://pepy.tech/project/mure)
[![downloads/month](https://static.pepy.tech/personalized-badge/mure?period=month&units=abbreviation&left_color=black&right_color=black&left_text=downloads/month)](https://pepy.tech/project/mure)
[![downloads/week](https://static.pepy.tech/personalized-badge/mure?period=week&units=abbreviation&left_color=black&right_color=black&left_text=downloads/week)](https://pepy.tech/project/mure)

This is a thin layer on top of [`httpx2`](https://httpx2.pydantic.dev/) that allows you to perform multiple HTTP requests concurrently without having to worry about async/await.

`mure` means **mu**ltiple **re**quests, but is also the German term for a form of mass wasting involving fast-moving flow of debris and dirt that has become liquified by the addition of water.

![Göscheneralp. Kolorierung des Dias durch Margrit Wehrli-Frey](https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/ETH-BIB-Muhrgang_zur_Kehlen-Reuss_vom_Rotfirn-Dia_247-13368.tif/lossy-page1-1280px-ETH-BIB-Muhrgang_zur_Kehlen-Reuss_vom_Rotfirn-Dia_247-13368.tif.jpg)

(The photo was taken by [Leo Wehrli](https://de.wikipedia.org/wiki/Leo_Wehrli) and is licensed under CC BY-SA 4.0)

## Installation

Install the latest stable version from [PyPI](https://pypi.org/project/mure):

```
pip install mure
```

## Usage

Pass a list of dictionaries with at least a value for `url` and get a generator with the corresponding responses. The first request is fired as soon as you access the first response:

```python
>>> import mure
>>> from mure.models import Resource
>>> resources: list[Resource] = [
...     {"url": "https://httpbin.org/get"},
...     {"url": "https://httpbin.org/get", "params": {"foo": "bar"}},
...     {"url": "invalid"},
... ]
>>> responses = mure.get(resources, batch_size=2)  # nothing fired yet
>>> for resource, response in zip(resources, responses):
...     print(resource, "status code:", response.status)
...
{'url': 'https://httpbin.org/get'} status code: 200
{'url': 'https://httpbin.org/get', 'params': {'foo': 'bar'}} status code: 200
{'url': 'invalid'} status code: 0
```

The number of requests fired at the same time will never exceed `batch_size`. This is a rolling window, not a barrier: `batch_size` workers pull from a shared iterator of requests, so the next request is fired as soon as any one of the in-flight requests finishes – there is no waiting for the whole batch to complete. Responses are still yielded in the order of the resources you passed in.

Nothing happens until you start consuming the generator, and if you stop early (e.g. by
breaking out of the loop), the requests that have not been fired yet are cancelled:

```python
>>> responses = mure.get(resources)  # nothing fired yet
>>> for response in responses:
...     if response.ok:
...         break  # the remaining resources are never requested
```

Redirects are followed and HTTP/2 is enabled by default. The connection pool is sized to
`batch_size`, so the number of open connections is bounded as well.

### Resources

A resource is a dictionary with at least a `url`. All other keys are optional:

| Key | Type | Description |
| --- | --- | --- |
| `url` | `str` | URL to request (required). |
| `headers` | `Mapping[str, str] \| None` | HTTP headers. |
| `params` | `Mapping[str, str] \| None` | URL parameters, merged with any query string already in `url`. |
| `data` | JSON serializable | Request body. |
| `json` | JSON serializable | JSON request body. |
| `timeout` | `int \| None` | Request timeout in seconds, by default 10, at most 30. |

```python
>>> resources = [
...     {
...         "url": "https://httpbin.org/post",
...         "headers": {"Authorization": "Bearer token"},
...         "params": {"foo": "bar"},
...         "json": {"lorem": "ipsum"},
...         "timeout": 30,
...     },
... ]
```

A request is never sent without a timeout: values greater than 30 seconds are capped at
30, and `None` (or a non-positive value) falls back to the default of 10 seconds.

### HTTP Methods

There are convenience functions for GET, POST, HEAD, PUT, PATCH and DELETE requests, for example:

```python
>>> resources = [
...     {"url": "https://httpbin.org/post"},
...     {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
...     {"url": "invalid"},
... ]
>>> responses = mure.post(resources)
```

### Responses

Each response has the following attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `ok` | `bool` | True if the status code indicates success. |
| `status` | `int` | HTTP status code (`0` if the request failed). |
| `reason` | `str \| None` | HTTP status reason (the `repr()` of the exception if the request failed). |
| `url` | `str` | Final URL after redirects. |
| `content` | `bytes` | Raw response body. |
| `encoding` | `str \| None` | Encoding reported by the server. |
| `headers` | `dict[str, str]` | Response headers. |
| `text` | `str` | Body decoded as text, falling back to encoding detection. |

Use `response.json()` to parse the body as JSON.

Requests never raise, which would otherwise interrupt the whole generator. A failed
request (invalid URL, connection error, timeout, ...) is a regular response with `ok` set
to `False`, `status` set to `0` and the exception in `reason`:

```python
>>> response = next(mure.get([{"url": "invalid"}]))
>>> response.ok, response.status
(False, 0)
>>> response.reason
'UnsupportedProtocol("Request URL is missing an \'http://\' or \'https://\' protocol.")'
```

So check `ok` (or `status`) rather than wrapping the loop in a `try`.

### Verbosity

Control verbosity with the `MURE_LOG_ERRORS` environment variable:

```python
>>> import os
>>> import mure
>>> next(mure.get([{"url": "invalid"}]))
<Response(0, UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol."))>
>>> os.environ["MURE_LOG_ERRORS"] = "true"
>>> next(mure.get([{"url": "invalid"}]))
[2026-06-10 13:19:22,546] [ERROR] Request URL is missing an 'http://' or 'https://' protocol.
Traceback (most recent call last):
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_transports/default.py", line 101, in map_httpcore_exceptions
    yield
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_transports/default.py", line 392, in handle_async_request
    resp = await self._pool.handle_async_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpcore2/_async/connection_pool.py", line 199, in handle_async_request
    raise UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol.")
httpcore2.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/severin/git/mure/mure/iterator.py", line 162, in _asend_request
    response = await session.send(_request, follow_redirects=session.follow_redirects)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_client.py", line 1582, in send
    response = await self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_client.py", line 1610, in _send_handling_auth
    response = await self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_client.py", line 1645, in _send_handling_redirects
    response = await self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_client.py", line 1679, in _send_single_request
    response = await transport.handle_async_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_transports/default.py", line 391, in handle_async_request
    with map_httpcore_exceptions():
         ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/severin/.local/share/mise/installs/python/3.14.4/lib/python3.14/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.14/site-packages/httpx2/_transports/default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx2.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.
<Response(0, UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol."))>
```

### Caching

You can enable caching to avoid requesting the same resources over and over again:

```python
>>> import mure
>>> from mure.cache import Cache
>>> resources = [
...     {"url": "https://httpbin.org/post"},
...     {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
...     {"url": "https://httpbin.org/post"},
... ]
>>> responses = mure.post(resources, cache=Cache.SQLITE)
```

This will make only two requests and use the hit from the cache for the last resource. Two resources are considered identical if the SHA256 hash over their method, URL, headers, parameters and body matches, so a changing header (e.g. a fresh token) is enough to miss the cache. The `timeout` is not part of the hash. The responses are stored in a local SQLite database `.mure-cache.sqlite` in the current working directory.

Note that you have to install [the SQLite extras](https://github.com/severinsimmler/mure/blob/master/pyproject.toml#L14-L17).

You can also use the in-memory storage with `Cache.MEMORY`. This cache only persists within the same function call, i.e. calling `mure.post()` twice will create two separate caches.

There is also a `Cache.FILE` which stores the responses on disk (in a folder `.mure-cache` in the current working directory).

> [!NOTE]
> Caching does not respect any `Cache-Control` HTTP headers or something like that. It just writes all responses, including unsuccessful ones, into the cache and may reuse them instead of firing another request. There is also no TTL mechanism.
