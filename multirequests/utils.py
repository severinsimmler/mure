from typing import Any, Iterator


def chunk(values: list[Any], n: int = 5) -> Iterator[Any]:
    """Splits the given list of values into batches of size `n`.

    Parameters
    ----------
    values : list[Any]
        Values to chunk.
    n : int, optional
        Number of items per batch, by default 5.

    Yields
    ------
    Iterator[Any]
        One batch at a time.
    """
    for i in range(0, len(values), n):
        yield values[i : i + n]
