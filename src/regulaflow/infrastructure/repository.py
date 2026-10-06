from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload, sessionmaker

from regulaflow.application.records import (
    BatchRecord,
    EventRecord,
    FindingRecord,
    OperationRecord,
    RunRecord,
)
from regulaflow.domain.errors import BatchNotFoundError
from regulaflow.domain.status import ProcessingStatus
from regulaflow.infrastructure.db import as_utc
from regulaflow.infrastructure.orm import (
    BatchRow,
    EventRow,
    FindingRow,
    OperationRow,
    RunRow,
)

_LOAD = (
    selectinload(BatchRow.operations),
    selectinload(BatchRow.runs).selectinload(RunRow.findings),
    selectinload(BatchRow.runs).selectinload(RunRow.events),
)


class SqlAlchemyBatchStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def ping(self) -> None:
        with self._factory() as session:
            session.execute(text("SELECT 1"))

    def get_by_identifier(self, identifier: str) -> BatchRecord | None:
        with self._factory() as session:
            statement = (
                select(BatchRow)
                .options(*_LOAD)
                .where(BatchRow.identifier == identifier)
            )
            row = session.scalar(statement)
            if row is None:
                return None
            return _to_batch(row)

    def get(self, batch_id: UUID) -> BatchRecord | None:
        with self._factory() as session:
            row = session.scalar(
                select(BatchRow).options(*_LOAD).where(BatchRow.id == batch_id)
            )
            if row is None:
                return None
            return _to_batch(row)

    def add(self, batch: BatchRecord) -> None:
        with self._factory() as session:
            session.add(_batch_row(batch))
            session.commit()

    def save_run(self, batch_id: UUID, run: RunRecord) -> BatchRecord:
        with self._factory() as session:
            row = session.scalar(
                select(BatchRow).options(*_LOAD).where(BatchRow.id == batch_id)
            )
            if row is None:
                raise BatchNotFoundError(str(batch_id))
            row.runs.append(_run_row(run))
            session.commit()
            return _to_batch(row)

    def list_batches(self) -> tuple[BatchRecord, ...]:
        with self._factory() as session:
            rows = session.scalars(
                select(BatchRow).options(*_LOAD).order_by(BatchRow.created_at.desc())
            )
            return tuple(_to_batch(row) for row in rows)


def _batch_row(batch: BatchRecord) -> BatchRow:
    return BatchRow(
        id=batch.id,
        identifier=batch.identifier,
        file_name=batch.file_name,
        reference_date=batch.reference_date,
        created_at=batch.created_at,
        operations=[
            OperationRow(
                id=uuid4(),
                position=index,
                identifier=item.identifier,
                amount=item.amount,
                occurred_on=item.occurred_on,
                movement_type=item.movement_type,
            )
            for index, item in enumerate(batch.operations)
        ],
        runs=[_run_row(item) for item in batch.runs],
    )


def _run_row(run: RunRecord) -> RunRow:
    return RunRow(
        id=run.id,
        status=run.status.value,
        started_at=run.started_at,
        finished_at=run.finished_at,
        operation_count=run.operation_count,
        error_count=run.error_count,
        warning_count=run.warning_count,
        error_operation_count=run.error_operation_count,
        findings=[
            FindingRow(
                id=uuid4(),
                position=index,
                code=item.code,
                description=item.description,
                severity=item.severity,
                operation_identifier=item.operation_identifier,
            )
            for index, item in enumerate(run.findings)
        ],
        events=[
            EventRow(
                id=uuid4(),
                position=index,
                action=item.action,
                created_at=item.created_at,
            )
            for index, item in enumerate(run.events)
        ],
    )


def _to_batch(row: BatchRow) -> BatchRecord:
    return BatchRecord(
        id=row.id,
        identifier=row.identifier,
        file_name=row.file_name,
        reference_date=row.reference_date,
        created_at=as_utc(row.created_at),
        operations=tuple(
            OperationRecord(
                item.identifier,
                item.amount,
                item.occurred_on,
                item.movement_type,
            )
            for item in row.operations
        ),
        runs=tuple(_to_run(item) for item in row.runs),
    )


def _to_run(row: RunRow) -> RunRecord:
    return RunRecord(
        id=row.id,
        status=ProcessingStatus(row.status),
        started_at=as_utc(row.started_at),
        finished_at=as_utc(row.finished_at),
        operation_count=row.operation_count,
        error_count=row.error_count,
        warning_count=row.warning_count,
        error_operation_count=row.error_operation_count,
        findings=tuple(
            FindingRecord(
                code=item.code,
                description=item.description,
                severity=item.severity,
                operation_identifier=item.operation_identifier,
            )
            for item in row.findings
        ),
        events=tuple(
            EventRecord(action=item.action, created_at=as_utc(item.created_at))
            for item in row.events
        ),
    )
