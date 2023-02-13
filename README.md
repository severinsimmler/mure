# mure

[![downloads](https://static.pepy.tech/personalized-badge/mure?period=total&units=international_system&left_color=black&right_color=black&left_text=downloads)](https://pepy.tech/project/mure)
[![downloads/month](https://static.pepy.tech/personalized-badge/mure?period=month&units=abbreviation&left_color=black&right_color=black&left_text=downloads/month)](https://pepy.tech/project/mure)
[![downloads/week](https://static.pepy.tech/personalized-badge/mure?period=week&units=abbreviation&left_color=black&right_color=black&left_text=downloads/week)](https://pepy.tech/project/mure)

This is a thin layer on top of [`aiohttp`](https://docs.aiohttp.org/en/stable/) to perform multiple HTTP requests in parallel – without writing boilerplate code or worrying about `async` functions.

`mure` means **mu**ltiple **re**quests, but is also the German term for a form of mass wasting involving fast-moving flow of debris and dirt that has become liquified by the addition of water.

![Göscheneralp. Kolorierung des Dias durch Margrit Wehrli-Frey](https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/ETH-BIB-Muhrgang_zur_Kehlen-Reuss_vom_Rotfirn-Dia_247-13368.tif/lossy-page1-1280px-ETH-BIB-Muhrgang_zur_Kehlen-Reuss_vom_Rotfirn-Dia_247-13368.tif.jpg)

(The photo was taken by [Leo Wehrli](https://de.wikipedia.org/wiki/Leo_Wehrli) and is licensed under CC BY-SA 4.0)

## Installation

Install the latest stable version from [PyPI](https://pypi.org/project/mure):

```
pip install mure
```

## Usage

Pass an iterable of dictionaries (a typed dictionary `Resource`, to be precise) with at least a value for `url` and get a `ResponseIterator` with the corresponding responses:

```python
>>> import mure
>>> from mure.dtos import Resource
>>> resources: list[Resource] = [
...     {"url": "https://httpbin.org/get"},
...     {"url": "https://httpbin.org/get", "params": {"foo": "bar"}},
...     {"url": "invalid"},
... ]
>>> responses = mure.get(resources, batch_size=2)
>>> responses
<ResponseIterator: 3 pending>
>>> for resource, response in zip(resources, responses):
...     print(resource, "status code:", response.status)
...
{'url': 'https://httpbin.org/get'} status code: 200
{'url': 'https://httpbin.org/get', 'params': {'foo': 'bar'}} status code: 200
{'url': 'invalid'} status code: 0
>>> responses
<ResponseIterator: 0 pending>
```

The keyword argument `batch_size` defines the number of requests to perform in parallel (don't be too greedy). The resources are requested batch-wise, i. e. only one batch of responses is kept in memory (depends of course also on how you use the `ResponseIterator`).

For example, if you set `batch_size` to `2`, have four resources and execute:

```python
>>> next(responses)
```

the first two resources are requested in parallel and blocks until both of the responses are available (i.e. if resource 1 takes 1 second and resource 2 takes 10 seconds, it blocks 10 seconds although resource 1 is already available after 1 second). The response of resource 1 is yielded.

Executing `next()` a second time:

```python
>>> next(response)
```

will be super fast, because the response of resource 2 is already available. Executing `next()` a third time will be "slow" again, because the next batch of resources is requested.

However, there is also a convenience function for POST requests:

```python
>>> resources = [
...     {"url": "https://httpbin.org/post"},
...     {"url": "https://httpbin.org/post", "json": {"foo": "bar"}},
...     {"url": "invalid"},
... ]
>>> responses = mure.post(resources)
```

You can even mix HTTP methods in the list of resources (but have to specify the method for each resource):

```python
>>> resources = [
...     {"method": "GET", "url": "https://httpbin.org/get"},
...     {"method": "GET", "url": "https://httpbin.org/get", "params": {"foo": "bar"}},
...     {"method": "POST", "url": "https://httpbin.org/post"},
...     {"method": "POST", "url": "https://httpbin.org/post", "json": {"foo": "bar"}},
...     {"method": "GET", "url": "invalid"},
... ]
>>> responses = mure.request(resources)
```

### Verbosity

Control verbosity with the `log_errors` argument:

```python
>>> import mure
>>> next(mure.get([{"url": "invalid"}], log_errors=True))
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
>>> next(mure.get([{"url": "invalid"}], log_errors=False))
Response(status=0, reason='<InvalidURL invalid>', ok=False, text='')
```
