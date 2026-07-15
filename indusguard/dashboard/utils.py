from __future__ import annotations

import json
from typing import Any

from sqlalchemy import inspect


def as_dict(instance: Any) -> dict[str, Any]:
    """Serialize only mapped columns, never SQLAlchemy internal state."""
    return {column.key: getattr(instance, column.key) for column in inspect(instance).mapper.column_attrs}


def json_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def envelope(data: Any, **meta: Any) -> dict[str, Any]:
    return {"data": data, "meta": meta}
