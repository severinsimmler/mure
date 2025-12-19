import hashlib
from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import Any, Literal, NotRequired, TypedDict
from urllib.parse import ParseResult, parse_qs, urlparse

import orjson
from charset_normalizer import from_bytes as detect_encoding

# supported http methods
Method = Literal["DELETE", "GET", "HEAD", "PATCH", "POST", "PUT"]

# json serializable types
Serializable = dict | list | str | int | float | bool | None


class Resource(TypedDict):
    """Resource to request."""

    url: str
    headers: NotRequired[Mapping[str, str] | None]
    params: NotRequired[Mapping[str, str] | None]
    data: NotRequired[Serializable]
    json: NotRequired[Serializable]
    timeout: NotRequired[int | None]


class Request:
    """HTTP request.

    Parameters
    ----------
    method : Literal["DELETE", "GET", "HEAD", "PATCH", "POST", "PUT"]
        HTTP method.
    url : str
        URL to request.
    headers : Mapping[str, str] | None, optional
        HTTP headers, by default None.
    params : Mapping[str, str] | None, optional
        URL parameters, by default None.
    data : Serializable, optional
        Request body, by default None.
    json : Serializable, optional
        JSON request body, by default None.
    timeout : int | None, optional
        Request timeout in seconds, by default 10.
    """

    def __init__(
        self,
        method: Method,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        data: Any | None = None,
        json: Any | None = None,
        timeout: int | None = 10,
    ):
        self.data = data
        self.json = json
        self.timeout = timeout
        self._method = method
        self._url = url
        self._headers = headers
        self._params = params

    def __repr__(self) -> str:
        """Return the string representation of the request."""
        return f"<Request({self.method}, {self.url})>"

    @property
    def method(self) -> str:
        """Return the HTTP method of the request."""
        return self._method.strip().upper()

    @property
    def url(self) -> str:
        """Return the URL of the request."""
        return f"{self.scheme}://{self.netloc}{self.path}"

    @cached_property
    def url_parts(self) -> ParseResult:
        """Return the parsed URL parts of the request."""
        return urlparse(self._url)

    @property
    def scheme(self) -> str:
        """Return the URL scheme of the request."""
        return self.url_parts.scheme

    @property
    def netloc(self) -> str:
        """Return the URL network location of the request."""
        return self.url_parts.netloc.lower()

    @property
    def path(self) -> str:
        """Return the URL path of the request."""
        return self.url_parts.path

    @cached_property
    def headers(self) -> dict[str, str] | None:
        """Return the HTTP headers of the request."""
        if self._headers is None:
            return None

        return {str(k).strip().lower(): str(v) for k, v in self._headers.items()}

    @cached_property
    def params(self) -> dict[str, list[str]] | None:
        """Return the URL parameters of the request."""
        params = parse_qs(self.url_parts.query)

        if self._params is None and not params:
            return None

        if self._params is not None:
            for key, value in self._params.items():
                if key in params:
                    params[key].append(value)
                else:
                    params[key] = [value]

        return params

    def sha256(self) -> str:
        """Return the digest value of a SHA256 hash as a string of hexadecimal digits."""
        data = orjson.dumps(
            {
                "method": self.method,
                "url": self.url,
                "headers": self._normalize(self.headers),
                "params": self._normalize(self.params),
                "data": self._normalize(self.data),
                "json": self._normalize(self.json),
            },
            option=orjson.OPT_SORT_KEYS,
        )

        return hashlib.sha256(data).hexdigest()

    def _normalize(self, value: Any) -> Any:
        """Normalize a value for hashing.

        Parameters
        ----------
        value : Any
            Value to normalize.

        Returns
        -------
        Any
            Normalized value.
        """
        if value is None:
            return None

        if isinstance(value, bytes):
            return {"__type": "bytes", "sha256": hashlib.sha256(value).hexdigest()}

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, Mapping):
            return {
                str(k): self._normalize(v)
                for k, v in sorted(value.items(), key=lambda item: str(item[0]))
            }

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [self._normalize(v) for v in value]

        try:
            return orjson.dumps(value, option=orjson.OPT_SORT_KEYS).decode("utf-8")
        except TypeError:
            return repr(value)


class Response:
    """HTTP response.

    Parameters
    ----------
    ok : bool
        True if the request was successful; otherwise, False.
    status : int
        HTTP status code.
    reason : str | None
        HTTP status reason.
    url : str
        URL of the response.
    text : str
        Response body.
    """

    def __init__(
        self,
        *,
        ok: bool,
        status: int,
        reason: str | None,
        url: str,
        content: bytes,
        encoding: str | None,
        headers: Mapping[str, str],
    ):
        self.ok = ok
        self.status = status
        self.reason = reason
        self.url = url
        self.content = content
        self.encoding = encoding
        self.headers = dict(headers)

    def __repr__(self) -> str:
        """Return the string representation of the response."""
        return f"<Response({self.status}, {self.reason})>"

    def json(self) -> Any:
        """Parse the response body as JSON.

        Returns
        -------
        Any
            Parsed JSON response body.
        """
        return orjson.loads(self.text)

    @cached_property
    def text(self) -> str:
        """Decode the response body as text.

        Returns
        -------
        str
            Decoded response body.
        """
        try:
            # try to decode the content using the response encoding
            return self.content.decode(self.encoding, errors="replace")  # type: ignore
        except (LookupError, TypeError):
            # LookupError is raised if the encoding was not found which could
            # indicate a misspelling or similar mistake
            #
            # TypeError can be raised if encoding is None
            if match := detect_encoding(self.content).best():
                return self.content.decode(match.encoding, errors="replace")

        raise ValueError("Unable to detect encoding for response content")
