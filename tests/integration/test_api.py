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
    movement_type: str = "ACQUISITION",
) -> dict[str, str]:
    return {
        "identifier": identifier,
        "amount": amount,
        "occurred_on": occurred_on,
        "movement_type": movement_type,
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
    panel = client.get("/api/painel").json()
    assert panel["file_types"] == []
    assert panel["success_rate"] == 0
    assert {item["label"] for item in panel["movements"]} == {
        "ACQUISITION",
        "SETTLEMENT",
        "TRANSFER",
        "REDEMPTION",
        "REVERSAL",
    }
    assert all(item["count"] == 0 for item in panel["movements"])
    assert all(item["count"] == 0 for item in panel["stages"])


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


def _findings(client: TestClient, **params: str) -> list[dict[str, str]]:
    response = client.get("/api/inconsistencias", params=params)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    return body


def test_finding_search_filters_the_latest_run(client: TestClient) -> None:
    created = client.post(
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
    assert created.status_code == 201
    clean = client.post(
        "/api/lotes",
        json=_payload("LOTE-OK", [_operation("OP9")]),
    )
    assert clean.status_code == 201
    listed = _findings(client)
    assert {item["code"] for item in listed} == {
        "VAL005",
        "VAL004",
        "VAL001",
        "VAL003",
    }
    assert _findings(client, regra="val005")[0]["code"] == "VAL005"
    assert _findings(client, regra="NOPE") == []
    warnings = _findings(client, severidade="WARNING")
    assert warnings
    assert all(item["severity"] == "WARNING" for item in warnings)
    assert _findings(client, severidade="INFO") == []
    by_operation = _findings(client, operacao="OP2")
    assert by_operation
    assert all("OP2" in item["operation_identifier"] for item in by_operation)
    assert _findings(client, operacao="ZZZ") == []
    assert _findings(client, lote="erro")
    assert _findings(client, lote="operacoes")
    assert _findings(client, lote="ausente") == []
    assert _findings(client, desde="2026-10-06T08:00:00")
    assert _findings(client, desde="2026-10-06T10:00:00Z") == []
    assert _findings(client, ate="2026-10-06T09:00:01Z") == []
    assert _findings(client, ate="2026-10-06T09:00:03Z")


def test_dashboard_groups_files_stages_and_movements(client: TestClient) -> None:
    first = client.post(
        "/api/lotes",
        json=_payload(
            "LOTE-A",
            [
                _operation(movement_type="SETTLEMENT"),
                _operation("OP2", movement_type="TRANSFER"),
            ],
        ),
    )
    assert first.status_code == 201
    assert first.json()["operations"][0]["movement_type"] == "SETTLEMENT"
    second_body = _payload("LOTE-B", [_operation("OP3")])
    second_body["file_name"] = "outro.csv"
    second = client.post("/api/lotes", json=second_body)
    assert second.status_code == 201
    plain = dict(_payload("LOTE-C", [_operation("OP4", movement_type="REVERSAL")]))
    plain["file_name"] = "lote"
    assert client.post("/api/lotes", json=plain).status_code == 201
    dotted = dict(_payload("LOTE-D", [_operation("OP5")]))
    dotted["file_name"] = "ops."
    assert client.post("/api/lotes", json=dotted).status_code == 201
    panel = client.get("/api/painel").json()
    files = {item["label"]: item["count"] for item in panel["file_types"]}
    assert files["csv"] == 2
    assert files["sem_extensao"] == 2
    movements = {item["label"]: item["count"] for item in panel["movements"]}
    assert movements["SETTLEMENT"] == 1
    assert movements["TRANSFER"] == 1
    assert movements["REVERSAL"] == 1
    assert movements["ACQUISITION"] == 2
    stages = {item["label"]: item["count"] for item in panel["stages"]}
    assert stages["COMPLETED"] == 4
    assert stages["FAILED"] == 0


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


def test_seed_demo_fills_an_empty_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = _url(tmp_path / "demo.db")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SEED_DEMO", "true")
    _migrate(url)
    with TestClient(create_app()) as client:
        first = client.get("/api/lotes").json()
    assert {item["identifier"] for item in first} == {
        "LOTE-SP-1042",
        "LOTE-RJ-1042",
        "LOTE-MG-1042",
        "LOTE-PR-1042",
    }
    rio = next(item for item in first if item["identifier"] == "LOTE-RJ-1042")
    assert rio["status"] == "COMPLETED_WITH_ERRORS"
    with TestClient(create_app()) as client:
        body = client.get("/api/lotes").json()
        metrics = client.get("/api/metricas").json()
    assert len(body) == 4
    assert metrics["average_seconds"] > 0


def test_database_helpers() -> None:
    aware = datetime(2026, 10, 6, tzinfo=UTC)
    assert as_utc(aware) is aware
    assert as_utc(datetime(2026, 10, 6)).tzinfo is UTC
    postgres = "postgresql+psycopg://regulaflow:regulaflow@localhost/regulaflow"
    remote = create_session_factory(postgres)
    remote.kw["bind"].dispose()
