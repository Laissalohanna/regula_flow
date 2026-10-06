from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from regulaflow.application.records import RunRecord
from regulaflow.composition.factory import create_app
from regulaflow.domain.errors import BatchNotFoundError
from regulaflow.domain.operations import Operation
from regulaflow.domain.rules import Finding
from regulaflow.domain.status import ProcessingStatus
from regulaflow.infrastructure.db import as_utc, create_session_factory
from regulaflow.infrastructure.repository import SqlAlchemyBatchStore


class TickingClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)

    def now(self) -> datetime:
        value = self.current
        self.current += timedelta(seconds=2)
        return value


def _url(path: Path) -> str:
    return "sqlite+pysqlite:///" + path.as_posix()


def _migrate(url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


def _payload(identifier: str, operations: list[dict[str, str]]) -> dict[str, object]:
    return {
        "identifier": identifier,
        "file_name": "operacoes.csv",
        "reference_date": "2026-10-01",
        "operations": operations,
    }


def _operation(
    identifier: str = "OP1",
    amount: str = "10.50",
    occurred_on: str = "2026-10-06",
) -> dict[str, str]:
    return {
        "identifier": identifier,
        "amount": amount,
        "occurred_on": occurred_on,
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = _url(tmp_path / "api.db")
    monkeypatch.setenv("DATABASE_URL", url)
    _migrate(url)
    app = create_app(database_url=url, clock=TickingClock())
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_empty_metrics(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/lotes").json() == []
    assert client.get("/api/metricas").json()["total"] == 0


def test_valid_batch_is_completed(client: TestClient) -> None:
    created = client.post("/api/lotes", json=_payload("LOTE-1", [_operation()]))
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "COMPLETED"
    listed = client.get("/api/lotes").json()
    assert listed[0]["identifier"] == "LOTE-1"
    detail = client.get(f"/api/lotes/{body['id']}").json()
    assert detail["runs"][0]["events"][0]["action"] == "Lote recebido"
    assert client.get("/api/metricas").json()["average_seconds"] == 2


def test_inconsistencies_are_stored(client: TestClient) -> None:
    response = client.post(
        "/api/lotes",
        json=_payload(
            "LOTE-ERRO",
            [
                _operation("OP1", "0"),
                _operation("OP1", "15.00"),
                _operation(" ", "10.00"),
                _operation("OP2", "8.00", "2026-11-02"),
            ],
        ),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED_WITH_ERRORS"
    codes = [item["code"] for item in body["runs"][0]["findings"]]
    assert "VAL005" in codes
    assert "VAL004" in codes
    assert "VAL001" in codes
    assert "VAL003" in codes


def test_duplicate_batch_returns_conflict(client: TestClient) -> None:
    payload = _payload("LOTE-1", [_operation()])
    assert client.post("/api/lotes", json=payload).status_code == 201
    conflict = client.post("/api/lotes", json=payload)
    assert conflict.status_code == 409


def test_missing_batch_returns_not_found(client: TestClient) -> None:
    missing = uuid4()
    assert client.get(f"/api/lotes/{missing}").status_code == 404
    assert client.post(f"/api/lotes/{missing}/reprocessamentos").status_code == 404


def test_reprocess_keeps_the_previous_run(client: TestClient) -> None:
    created = client.post(
        "/api/lotes",
        json=_payload("LOTE-ERRO", [_operation(amount="0")]),
    )
    batch_id = created.json()["id"]
    again = client.post(f"/api/lotes/{batch_id}/reprocessamentos")
    assert again.status_code == 201
    runs = again.json()["runs"]
    assert [item["status"] for item in runs] == [
        "COMPLETED_WITH_ERRORS",
        "COMPLETED_WITH_ERRORS",
    ]
    assert runs[1]["events"][0]["action"] == "Processamento reprocessado"


def test_completed_batch_cannot_be_reprocessed(client: TestClient) -> None:
    created = client.post("/api/lotes", json=_payload("LOTE-OK", [_operation()]))
    batch_id = created.json()["id"]
    response = client.post(f"/api/lotes/{batch_id}/reprocessamentos")
    assert response.status_code == 409


def test_empty_operations_are_rejected(client: TestClient) -> None:
    response = client.post("/api/lotes", json=_payload("LOTE-VAZIO", []))
    assert response.status_code == 422


def test_warning_does_not_fail_the_batch(client: TestClient) -> None:
    response = client.post(
        "/api/lotes",
        json=_payload("LOTE-AVISO", [_operation(occurred_on="2026-12-01")]),
    )
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["runs"][0]["warning_count"] == 1


def test_technical_failure_marks_the_batch(tmp_path: Path) -> None:
    url = _url(tmp_path / "fail.db")
    _migrate(url)

    def explode(
        _operations: Sequence[Operation],
        _reference_date: object,
    ) -> tuple[Finding, ...]:
        raise RuntimeError("boom")

    app = create_app(database_url=url, evaluator=explode)
    with TestClient(app) as client:
        response = client.post(
            "/api/lotes",
            json=_payload("LOTE-FALHA", [_operation()]),
        )
    assert response.status_code == 500
    batch_id = response.json()["batch_id"]
    with TestClient(create_app(database_url=url)) as client:
        detail = client.get(f"/api/lotes/{batch_id}")
    assert detail.json()["status"] == "FAILED"


def test_app_reads_database_url_from_the_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = _url(tmp_path / "env.db")
    monkeypatch.setenv("DATABASE_URL", url)
    _migrate(url)
    with TestClient(create_app()) as client:
        response = client.post("/api/lotes", json=_payload("LOTE-ENV", [_operation()]))
    assert response.status_code == 201


def test_health_reports_unavailable_store() -> None:
    class DownStore:
        def ping(self) -> None:
            raise RuntimeError("down")

    with TestClient(create_app(store=DownStore())) as client:
        response = client.get("/health")
    assert response.status_code == 503


def test_save_run_for_unknown_batch(tmp_path: Path) -> None:
    url = _url(tmp_path / "store.db")
    _migrate(url)
    store = SqlAlchemyBatchStore(create_session_factory(url))
    moment = datetime(2026, 10, 6, tzinfo=UTC)
    run = RunRecord(
        id=uuid4(),
        status=ProcessingStatus.FAILED,
        started_at=moment,
        finished_at=moment,
        operation_count=0,
        error_count=0,
        warning_count=0,
        error_operation_count=0,
        findings=(),
        events=(),
    )
    with pytest.raises(BatchNotFoundError):
        store.save_run(uuid4(), run)


def test_database_helpers() -> None:
    aware = datetime(2026, 10, 6, tzinfo=UTC)
    assert as_utc(aware) is aware
    assert as_utc(datetime(2026, 10, 6)).tzinfo is UTC
    postgres = "postgresql+psycopg://regulaflow:regulaflow@localhost/regulaflow"
    remote = create_session_factory(postgres)
    remote.kw["bind"].dispose()
