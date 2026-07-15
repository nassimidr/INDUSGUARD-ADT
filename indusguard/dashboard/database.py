from __future__ import annotations
from pathlib import Path
from sqlalchemy import create_engine,event,text
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from .config import DashboardConfig

class Base(DeclarativeBase):pass

def build_engine(config:DashboardConfig):
    url=config.database_url
    if url.startswith("sqlite:///"):
        Path(url[10:]).parent.mkdir(parents=True,exist_ok=True)
    engine=create_engine(url,echo=bool(config.values["database"].get("echo",False)),connect_args={"check_same_thread":False} if url.startswith("sqlite") else {})
    if url.startswith("sqlite") and config.values["database"].get("wal_mode",True):
        @event.listens_for(engine,"connect")
        def _sqlite(dbapi_connection,_):
            cursor=dbapi_connection.cursor();cursor.execute("PRAGMA journal_mode=WAL");cursor.execute("PRAGMA foreign_keys=ON");cursor.close()
    return engine

def session_factory(engine):return sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
def initialize_database(engine)->None:
    from . import models
    Base.metadata.create_all(engine)
