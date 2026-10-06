from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from tests.memory_store import MemoryBatchStore

from regulaflow.application.errors import ProcessingFailureError
from regulaflow.application.service import BatchCommand, BatchService, Evaluator
from regulaflow.domain.errors import (
    BatchNotFoundError,
    DuplicateBatchError,
    NotReprocessableError,
)
from regulaflow.domain.operations import Operation
from regulaflow.domain.rules import Finding, evaluate
from regulaflow.domain.status import ProcessingStatus

REFERENCE = date(2026, 10, 1)


class TickingClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)

    def now(self) -> datetime:
        value = self.current
        self.current += timedelta(seconds=2)
        return value


def _operation(identifier: str = "OP1", amount: str = "10.00") -> Operation:
    return Operation(identifier, Decimal(amount), date(2026, 10, 6))


def _command(*operations: Operation, identifier: str = "LOTE-1") -> BatchCommand:
    return BatchCommand(
        identifier=identifier,
        file_name="operacoes.csv",
        reference_date=REFERENCE,
        operations=operations or (_operation(),),
    )


def _service(
    store: MemoryBatchStore | None = None,
    evaluator: Evaluator | None = None,
) -> tuple[BatchService, MemoryBatchStore]:
    memory = store or MemoryBatchStore()
    return BatchService(memory, TickingClock(), evaluator), memory


def test_receive_completed_batch_and_lists_newest_first() -> None:
    service, _store = _service()
    first = service.receive(_command(identifier="LOTE-1"))
    second = service.receive(_command(_operation("OP2"), identifier="LOTE-2"))

    assert first.current_status is ProcessingStatus.COMPLETED
    assert [item.action for item in first.runs[0].events] == [
        "Lote recebido",
        "Processamento iniciado",
        "Processamento finalizado",
    ]
    assert [item.identifier for item in service.list_batches()] == ["LOTE-2", "LOTE-1"]
    assert service.get(second.id).identifier == "LOTE-2"
    assert service.metrics().success_rate == 100
    service.ping()


def test_inconsistencies_keep_one_event_per_rule() -> None:
    service, _store = _service()
    outside = Operation("OP3", Decimal("8.00"), date(2026, 11, 2))
    batch = service.receive(
        _command(_operation("OP1", "0"), _operation("OP2", "-4"), outside)
    )
    actions = [item.action for item in batch.runs[0].events]
    assert batch.current_status is ProcessingStatus.COMPLETED_WITH_ERRORS
    assert actions.count("Regra VAL005 executada") == 1
    assert "Regra VAL003 executada" in actions
    assert batch.runs[0].error_count == 2
    assert batch.runs[0].warning_count == 1


def test_duplicate_batch_is_rejected() -> None:
    service, _store = _service()
    service.receive(_command())
    with pytest.raises(DuplicateBatchError):
        service.receive(_command())


def test_missing_batch() -> None:
    service, _store = _service()
    missing = uuid4()
    with pytest.raises(BatchNotFoundError):
        service.get(missing)
    with pytest.raises(BatchNotFoundError):
        service.reprocess(missing)


def test_completed_batch_cannot_be_reprocessed() -> None:
    service, _store = _service()
    batch = service.receive(_command())
    with pytest.raises(NotReprocessableError):
        service.reprocess(batch.id)


def test_reprocess_appends_a_run_and_keeps_the_previous_one() -> None:
    service, store = _service()
    batch = service.receive(_command(_operation(amount="0")))
    updated = service.reprocess(batch.id)
    stored = store.get(batch.id)
    assert stored is not None
    assert len(updated.runs) == 2
    assert stored.runs[0].status is ProcessingStatus.COMPLETED_WITH_ERRORS
    assert stored.runs[1].status is ProcessingStatus.COMPLETED_WITH_ERRORS
    assert stored.runs[1].events[0].action == "Processamento reprocessado"


def test_technical_failure_is_stored_as_failed() -> None:
    def explode(
        _operations: Sequence[Operation],
        _reference_date: date,
    ) -> tuple[Finding, ...]:
        raise RuntimeError("boom")

    service, store = _service(evaluator=explode)
    with pytest.raises(ProcessingFailureError) as captured:
        service.receive(_command())
    stored = store.get(captured.value.batch_id)
    assert stored is not None
    assert stored.current_status is ProcessingStatus.FAILED


def test_reprocess_failure_keeps_the_original_run() -> None:
    calls = {"count": 0}

    def flaky(
        operations: Sequence[Operation],
        reference_date: date,
    ) -> tuple[Finding, ...]:
        calls["count"] += 1
        if calls["count"] > 1:
            raise RuntimeError("boom")
        return evaluate(operations, reference_date)

    service, store = _service(evaluator=flaky)
    batch = service.receive(_command(_operation(amount="0")))
    with pytest.raises(ProcessingFailureError):
        service.reprocess(batch.id)
    stored = store.get(batch.id)
    assert stored is not None
    assert stored.runs[0].status is ProcessingStatus.COMPLETED_WITH_ERRORS
    assert stored.runs[1].status is ProcessingStatus.FAILED
