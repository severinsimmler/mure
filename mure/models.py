import json
from typing import Any, Literal, Mapping, NotRequired, TypedDict

Method = Literal["DELETE", "GET", "HEAD", "PATCH", "POST", "PUT"]


class Resource(TypedDict):
    """Resource to request."""

    url: str
    headers: NotRequired[Mapping[str, str] | None]
    params: NotRequired[Mapping[str, str] | None]
    data: NotRequired[Any | None]
    json: NotRequired[Any | None]
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
    data : Any | None, optional
        Request body, by default None.
    json : Any | None, optional
        JSON request body, by default None.
    timeout : int | None, optional
        Request timeout in seconds, by default None.
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
        timeout: int | None = None,
    ):
        self.method = method
        self.url = url
        self.headers = headers
        self.params = params
        self.data = data
        self.json = json
        self.timeout = timeout

    def __hash__(self) -> int:
        """Hash the request."""
        return hash(
            (
                self.method,
                self.url,
                json.dumps(self.params, sort_keys=True, ensure_ascii=False).lower(),
                json.dumps(self.json, sort_keys=True, ensure_ascii=False).lower(),
                self.data
                if isinstance(self.data, (str, bytes))
                else json.dumps(self.data, sort_keys=True, ensure_ascii=False),
            )
        )

    def __eq__(self, other: "Request") -> bool:
        """Check if two requests are equal.

        Parameters
        ----------
        other : Request
            Other request to compare.

        Returns
        -------
        bool
            True if the requests are equal; otherwise, False.
        """
        return (
            isinstance(other, Request)
            and self.method == other.method
            and self.url == other.url
            and self.params == other.params
            and self.data == other.data
        )


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
        text: str,
    ):
        self.ok = ok
        self.status = status
        self.reason = reason
        self.url = url
        self.text = text
