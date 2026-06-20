from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from manotron.models import Base


def make_engine(db_path: str | Path) -> Engine:
    path = Path(db_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", future=True)


def init_db(db_path: str | Path) -> None:
    engine = make_engine(db_path)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(db_path: str | Path) -> Iterator[Session]:
    engine = make_engine(db_path)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

