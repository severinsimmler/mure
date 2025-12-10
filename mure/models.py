from collections.abc import Mapping
from functools import cached_property
from typing import Any, Literal, NotRequired, TypedDict

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
        self.method = method
        self.url = url
        self.headers = headers
        self.params = params
        self.data = data
        self.json = json
        self.timeout = timeout

    def __repr__(self) -> str:
        """Return the string representation of the request."""
        return f"<Request({self.method}, {self.url})>"


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
        self.headers = headers

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
