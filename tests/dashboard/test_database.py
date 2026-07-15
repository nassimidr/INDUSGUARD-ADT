from sqlalchemy import inspect

from indusguard.dashboard.models import ALL_MODELS


def test_all_fifteen_tables_are_created(app):
    tables = set(inspect(app.state.engine).get_table_names())
    assert len(ALL_MODELS) == 15
    assert {model.__tablename__ for model in ALL_MODELS} <= tables


def test_sqlite_foreign_keys_and_wal_are_enabled(app):
    with app.state.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "wal"
