"""Versioned route files shared by the desktop app and CLI."""

import json
import os
import tempfile
from pathlib import Path

from .core import Journey, ValidationError

MAX_FILE_BYTES = 128 * 1024


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"Duplicate JSON field: {key}.")
        result[key] = value
    return result


def loads_route(text: str) -> Journey:
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValidationError("Route file exceeds 128 KiB.")
    try:
        data = json.loads(text, object_pairs_hook=_unique_object)
    except (ValueError, RecursionError) as exc:
        raise ValidationError(f"Invalid route JSON: {exc}") from exc
    return Journey.from_dict(data)


def load_route(path: str | Path) -> Journey:
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValidationError("Route file exceeds 128 KiB.")
    try:
        return loads_route(data.decode("utf-8-sig"))
    except UnicodeError as exc:
        raise ValidationError("Route file must use UTF-8 encoding.") from exc


def save_route(path: str | Path, journey: Journey) -> None:
    """Replace only after a complete write; keep the previous file if writing fails."""
    path = Path(path)
    text = json.dumps(journey.to_dict(), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
