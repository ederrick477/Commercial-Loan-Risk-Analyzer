from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


def _default_db_path() -> Path:
	root = Path(__file__).resolve().parents[1]
	return root / "loans.db"


def get_database_url() -> str:
	path = os.environ.get("LOANS_DB_PATH")
	if path:
		return f"sqlite:///{path}"
	return f"sqlite:///{_default_db_path()}"


engine = create_engine(get_database_url(), echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def init_db() -> None:
	Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Session:
	session: Session = SessionLocal()
	try:
		yield session
		session.commit()
	except Exception:
		session.rollback()
		raise
	finally:
		session.close()
