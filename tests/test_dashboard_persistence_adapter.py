import logging
import queue

from indusguard.multi_agent.adapters.dashboard_persistence_adapter import (
    DashboardPersistenceAdapter,
)


def test_full_dashboard_queue_is_observable(caplog):
    adapter = DashboardPersistenceAdapter.__new__(DashboardPersistenceAdapter)
    adapter.queue = queue.Queue(maxsize=1)
    adapter.queue.put_nowait(("event", {}))

    with caplog.at_level(logging.WARNING):
        adapter.submit("domain", {"message_type": "sensor.measurement"})

    assert "queue is full" in caplog.text
    assert "kind=domain" in caplog.text


def test_dashboard_database_failure_is_observable(caplog):
    adapter = DashboardPersistenceAdapter.__new__(DashboardPersistenceAdapter)
    adapter.queue = queue.Queue()
    adapter.queue.put(("event", {"message_type": "audit.event"}))
    adapter.queue.put(None)

    def unavailable_session():
        raise RuntimeError("database unavailable")

    adapter.Session = unavailable_session

    with caplog.at_level(logging.ERROR):
        adapter._consume()

    assert "Dashboard persistence failed" in caplog.text
    assert "database unavailable" in caplog.text
