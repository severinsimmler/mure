# mure

[![downloads](https://static.pepy.tech/personalized-badge/mure?period=total&units=international_system&left_color=black&right_color=black&left_text=downloads)](https://pepy.tech/project/mure)
[![downloads/month](https://static.pepy.tech/personalized-badge/mure?period=month&units=abbreviation&left_color=black&right_color=black&left_text=downloads/month)](https://pepy.tech/project/mure)
[![downloads/week](https://static.pepy.tech/personalized-badge/mure?period=week&units=abbreviation&left_color=black&right_color=black&left_text=downloads/week)](https://pepy.tech/project/mure)

This is a thin layer on top of [`httpx`](https://www.python-httpx.org/) to perform multiple HTTP requests concurrently – without worrying about async/await.

`mure` means **mu**ltiple **re**quests, but is also the German term for a form of mass wasting involving fast-moving flow of debris and dirt that has become liquified by the addition of water.

![Göscheneralp. Kolorierung des Dias durch Margrit Wehrli-Frey](https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/ETH-BIB-Muhrgang_zur_Kehlen-Reuss_vom_Rotfirn-Dia_247-13368.tif/lossy-page1-1280px-ETH-BIB-Muhrgang_zur_Kehlen-Reuss_vom_Rotfirn-Dia_247-13368.tif.jpg)

(The photo was taken by [Leo Wehrli](https://de.wikipedia.org/wiki/Leo_Wehrli) and is licensed under CC BY-SA 4.0)

## Installation

Install the latest stable version from [PyPI](https://pypi.org/project/mure):

```
pip install mure
```

## Usage

Pass a list of dictionaries with at least a value for `url` and get a `ResponseIterator` with the corresponding responses. The first request is fired as soon as you access the first response:

```python
>>> import mure
>>> from mure.models import Resource
>>> resources: list[Resource] = [
...     {"url": "https://httpbin.org/get"},
...     {"url": "https://httpbin.org/get", "params": {"foo": "bar"}},
...     {"url": "invalid"},
... ]
>>> responses = mure.get(resources, batch_size=2)
>>> responses
<ResponseIterator: 3/3 pending>
>>> for resource, response in zip(resources, responses):
...     print(resource, "status code:", response.status)
...
{'url': 'https://httpbin.org/get'} status code: 200
{'url': 'https://httpbin.org/get', 'params': {'foo': 'bar'}} status code: 200
{'url': 'invalid'} status code: 0
>>> responses
<ResponseIterator: 0/3 pending>
```

The keyword argument `batch_size` defines the number of requests to perform concurrently. The resources are requested lazy and in batches, i.e. only one batch of responses is kept in memory. Once you start accessing the first response of a batch, the next resource is requested already in the background.

For example, if you have four resources, set `batch_size` to `2` and execute:

```python
>>> next(responses)
```

the first two resources are requested concurrently and block until both of the responses are available (i.e. if resource 1 takes 1 second and resource 2 takes 10 seconds, it blocks 10 seconds although resource 1 is already available after 1 second). Before the response of resource 1 is yielded, the next batch of resources (i.e. 3 and 4) is already requested in the background.

Executing `next()` a second time:

```python
>>> next(responses)
```

will be super fast, because the response of resource 2 is already available (1 and 2 were in the same batch).

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

### Verbosity

Control verbosity with the `MURE_LOG_ERRORS` environment variable:

```python
>>> import os
>>> import mure
>>> next(mure.get([{"url": "invalid"}]))
<Response(0, UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol."))>
>>> os.environ["MURE_LOG_ERRORS"] = "true"
>>> next(mure.get([{"url": "invalid"}]))
[2024-05-17 10:23:21,963] [ERROR] Request URL is missing an 'http://' or 'https://' protocol.
Traceback (most recent call last):
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_transports/default.py", line 69, in map_httpcore_exceptions
    yield
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_transports/default.py", line 373, in handle_async_request
    resp = await self._pool.handle_async_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpcore/_async/connection_pool.py", line 167, in handle_async_request
    raise UnsupportedProtocol(
httpcore.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/severin/git/mure/mure/iterator.py", line 266, in _afetch
    response = await session.request(
               ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_client.py", line 1574, in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_client.py", line 1661, in send
    response = await self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_client.py", line 1689, in _send_handling_auth
    response = await self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_client.py", line 1726, in _send_handling_redirects
    response = await self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_client.py", line 1763, in _send_single_request
    response = await transport.handle_async_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_transports/default.py", line 372, in handle_async_request
    with map_httpcore_exceptions():
  File "/home/severin/.pyenv/versions/3.12.2/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/home/severin/git/mure/.venv/lib/python3.12/site-packages/httpx/_transports/default.py", line 86, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.
<Response(0, UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol."))>
```

### Caching

You can enable caching (powered by [`hishel`](https://hishel.com/)) to avoid requesting the same resources over and over again:

```python
>>> import mure
>>> from mure.cache import Cache
>>> resources = [
...     {"url": "https://httpbin.org/post"},
...     {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
...     {"url": "https://httpbin.org/post"},
... ]
>>> responses = mure.post(resources, cache=Cache.FILE)
```

This will make only two requests and use the hit from the cache for the last resource. Currently, three types of caches are supported:

- `Cache.IN_MEMORY` will hold it in memory
- `Cache.FILE` will store reponses on-disk in a folder `.cache`
- `Cache.SQLITE` will store responses in a SQLite database `.hishel.sqlite`

### `OSError: [Errno 24] Too many open files`

This error typically occurs when your process tries to open more file descriptors (often network sockets in this context) than the operating system allows per process.

Each concurrent request within the `batch_size` potentially opens a socket. If `batch_size` is large or requests are slow, you can hit the system's limit.

You can either increase the limit temporarily for the current shell session:

```
$ ulimit -n 65536
```

or reduce the `batch_size`.
