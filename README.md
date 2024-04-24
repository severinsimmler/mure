# mure

[![downloads](https://static.pepy.tech/personalized-badge/mure?period=total&units=international_system&left_color=black&right_color=black&left_text=downloads)](https://pepy.tech/project/mure)
[![downloads/month](https://static.pepy.tech/personalized-badge/mure?period=month&units=abbreviation&left_color=black&right_color=black&left_text=downloads/month)](https://pepy.tech/project/mure)
[![downloads/week](https://static.pepy.tech/personalized-badge/mure?period=week&units=abbreviation&left_color=black&right_color=black&left_text=downloads/week)](https://pepy.tech/project/mure)

This is a thin layer on top of [`aiohttp`](https://docs.aiohttp.org/en/stable/) to perform multiple HTTP requests concurrently – without worrying about async/await.

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
Response(status=0, reason='<InvalidURL invalid>', ok=False, text='')
>>> os.environ["MURE_LOG_ERRORS"] = "true"
>>> next(mure.get([{"url": "invalid"}]))
invalid
Traceback (most recent call last):
  File "/home/severin/git/mure/mure/iterator.py", line 131, in _process
    async with session.request(resource["method"], resource["url"], **kwargs) as response:
  File "/home/severin/git/mure/.env/lib/python3.11/site-packages/aiohttp/client.py", line 1141, in __aenter__
    self._resp = await self._coro
                 ^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.env/lib/python3.11/site-packages/aiohttp/client.py", line 508, in _request
    req = self._request_class(
          ^^^^^^^^^^^^^^^^^^^^
  File "/home/severin/git/mure/.env/lib/python3.11/site-packages/aiohttp/client_reqrep.py", line 305, in __init__
    self.update_host(url)
  File "/home/severin/git/mure/.env/lib/python3.11/site-packages/aiohttp/client_reqrep.py", line 364, in update_host
    raise InvalidURL(url)
aiohttp.client_exceptions.InvalidURL: invalid
Response(status=0, reason='<InvalidURL invalid>', ok=False, text='')
```

### Caching

You can cache responses either in-memory (`MemoryCache`) or on your disk (`DiskCache`) to avoid requesting the same resources over and over again:

```python
>>> import mure
>>> from mure.cache import DiskCache
>>> cache = DiskCache()
>>> resources = [
...     {"url": "https://httpbin.org/post"},
...     {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
... ]
>>> responses = mure.post(resources, cache=cache)
```

`MemoryCache` holds requests and corresponding responses in a simple dictionary in memory, `DiskCache` is serializing to disk using Python's `shelve` module from the standard library.
