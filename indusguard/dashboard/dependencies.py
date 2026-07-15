from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.Session()
    try:
        yield session
    finally:
        session.close()
