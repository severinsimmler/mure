from dataclasses import dataclass
from typing import Any, TypedDict

import orjson


class Resource(TypedDict):
    method: str
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
    """

    status: int
    reason: str
    ok: bool
    text: str

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
