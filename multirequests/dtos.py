from typing import TypedDict


class Resource(TypedDict):
    method: str
    url: str


class Response(TypedDict):
    status: int
    reason: str
    ok: bool
    body: str
