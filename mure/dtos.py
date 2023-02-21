from dataclasses import dataclass
from ssl import SSLContext
from types import SimpleNamespace
from typing import Any, Iterable, Literal, Mapping, TypedDict
from urllib.parse import urlparse

import orjson
from aiohttp import BasicAuth, ClientTimeout, Fingerprint
from aiohttp.typedefs import LooseCookies, LooseHeaders, StrOrURL

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


# allowed http methods
HTTPMethod = Literal["GET", "POST", "HEAD", "PUT", "PATCH", "DELETE"]


class Resource(TypedDict):
    """Resource with at least a URL specified."""

    url: str
    params: NotRequired[Mapping[str, str] | None]
    data: NotRequired[Any]
    json: NotRequired[Any]
    cookies: NotRequired[LooseCookies | None]
    headers: NotRequired[LooseHeaders | None]
    skip_auto_headers: NotRequired[Iterable[str] | None]
    auth: NotRequired[BasicAuth | None]
    allow_redirects: NotRequired[bool]
    max_redirects: NotRequired[int]
    compress: NotRequired[str | None]
    chunked: NotRequired[bool | None]
    expect100: NotRequired[bool]
    raise_for_status: NotRequired[bool | None]
    read_until_eof: NotRequired[bool]
    proxy: NotRequired[StrOrURL | None]
    proxy_auth: NotRequired[BasicAuth | None]
    timeout: NotRequired[ClientTimeout | object]
    verify_ssl: NotRequired[bool | None]
    fingerprint: NotRequired[bytes | None]
    ssl_context: NotRequired[SSLContext | None]
    ssl: NotRequired[SSLContext | bool | Fingerprint | None]
    proxy_headers: NotRequired[LooseHeaders | None]
    trace_request_ctx: NotRequired[SimpleNamespace | None]
    read_bufsize: NotRequired[int | None]


class HTTPResource(Resource):
    """HTTP resources with at least a URL and HTTP method specified."""

    method: HTTPMethod


@dataclass
class HistoricResponse:
    """Historic HTTP response.

    Attributes
    ----------
    status : int
        HTTP status code of response, e.g. 200.
    reason : str
        HTTP status reason of response, e.g. "OK".
    ok : bool
        Boolean representation of HTTP status code. True if status is <400; otherwise, False.
    url : str
        Response URL.
    """

    status: int
    reason: str
    ok: bool
    url: str


@dataclass
class Response:
    """HTTP response.

    Attributes
    ----------
    status : int
        HTTP status code of response, e.g. 200.
    reason : str
        HTTP status reason of response, e.g. "OK".
    ok : bool
        Boolean representation of HTTP status code. True if status is <400; otherwise, False.
    text : str
        Response's body as decoded string.
    url : str
        Response URL.
    history : list[HistoricResponse]
        List of historic responses (in case requested URL redirected).
    """

    status: int
    reason: str
    ok: bool
    text: str
    url: str
    history: list[HistoricResponse]

    def json(self) -> Any:
        """Deserialize JSON to Python objects.

        Returns
        -------
        Any
            Parsed Python objects.
        """
        return orjson.loads(self.text)

    def __getitem__(self, attr: str) -> int | str | bool:
        """Get the specified attribute.

        Parameters
        ----------
        attr : str
            Attribute to get.

        Returns
        -------
        int | str | bool
            Attribute value.
        """
        return getattr(self, attr)

    def is_same_netloc(self, url: str) -> bool:
        """True if the given URL has the same netloc as the response URL.

        Parameters
        ----------
        url : str
            URL to check.

        Returns
        -------
        bool
            True if same netloc, False otherwise.
        """
        a = urlparse(url)
        b = urlparse(self.url)
        return a.netloc.lower() == b.netloc.lower()
