# mure

[![downloads](https://static.pepy.tech/personalized-badge/mure?period=total&units=international_system&left_color=black&right_color=black&left_text=downloads)](https://pepy.tech/project/mure)
[![downloads/month](https://static.pepy.tech/personalized-badge/mure?period=month&units=abbreviation&left_color=black&right_color=black&left_text=downloads/month)](https://pepy.tech/project/mure)
[![downloads/week](https://static.pepy.tech/personalized-badge/mure?period=week&units=abbreviation&left_color=black&right_color=black&left_text=downloads/week)](https://pepy.tech/project/mure)

This is a thin layer on top of [`aiohttp`](https://docs.aiohttp.org/en/stable/) to perform multiple HTTP requests in parallel – without writing boilerplate code or worrying about `async` functions.

> `mure` means **mu**ltiple **re**quests, but is also the German term for a form of mass wasting involving fast-moving flow of debris and dirt that has become liquified by the addition of water.

Install the latest stable version from [PyPI](https://pypi.org/project/mure):

```
pip install mure
```

## Usage

Pass an iterable of dictionaries with at least a value for `url` and get `ResponseIterator` with the responses:

```python
>>> import mure
>>> resources = [
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
```

The keyword argument `batch_size` defines the number of requests to perform in parallel (don't be too greedy).

There is also a convenience function for POST requests:

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
