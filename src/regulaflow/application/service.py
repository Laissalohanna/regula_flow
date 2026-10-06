from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID, uuid4

from regulaflow.application.clock import Clock
from regulaflow.application.errors import ProcessingFailureError
from regulaflow.application.records import (
    BatchRecord,
    EventRecord,
    FindingHit,
    FindingRecord,
    OperationRecord,
    RunRecord,
)
from regulaflow.application.store import BatchStore
from regulaflow.domain.errors import (
    BatchNotFoundError,
    DuplicateBatchError,
    NotReprocessableError,
)
from regulaflow.domain.metrics import ProcessingMetrics, RunSnapshot, summarize
from regulaflow.domain.operations import Operation
from regulaflow.domain.rules import Finding, Severity, evaluate
from regulaflow.domain.status import ProcessingState, ProcessingStatus


@dataclass(frozen=True, slots=True)
class FindingQuery:
    batch: str = ""
    operation: str = ""
    code: str = ""
    severity: str = ""
    since: datetime | None = None
    until: datetime | None = None


class Evaluator(Protocol):
    def __call__(
        self,
        operations: Sequence[Operation],
        reference_date: date,
    ) -> Sequence[Finding]: ...


_REPROCESSABLE = frozenset(
    {
        ProcessingStatus.FAILED,
        ProcessingStatus.COMPLETED_WITH_ERRORS,
    }
)


@dataclass(frozen=True, slots=True)
class BatchCommand:
    identifier: str
    file_name: str
    reference_date: date
    operations: tuple[Operation, ...]


class _RunAbortedError(Exception):
    def __init__(self, run: RunRecord) -> None:
        self.run = run
        super().__init__("run aborted")


class BatchService:
    def __init__(
        self,
        store: BatchStore,
        clock: Clock,
        evaluator: Evaluator | None = None,
    ) -> None:
        self._store = store
        self._clock = clock
        self._evaluator = evaluator if evaluator is not None else evaluate

    def ping(self) -> None:
        self._store.ping()

    def receive(self, command: BatchCommand) -> BatchRecord:
        if self._store.get_by_identifier(command.identifier) is not None:
            raise DuplicateBatchError(command.identifier)
        try:
            run = self._execute(
                command.operations,
                command.reference_date,
                ("Lote recebido",),
                ProcessingState.received(),
            )
        except _RunAbortedError as aborted:
            batch = self._batch(command, aborted.run)
            self._store.add(batch)
            raise ProcessingFailureError(batch.id) from aborted
        batch = self._batch(command, run)
        self._store.add(batch)
        return batch

    def reprocess(self, batch_id: UUID) -> BatchRecord:
        batch = self._require(batch_id)
        if batch.current_status not in _REPROCESSABLE:
            raise NotReprocessableError(batch.current_status.value)
        initial = ProcessingState(status=batch.current_status).transition_to(
            ProcessingStatus.REPROCESSING
        )
        try:
            run = self._execute(
                _operations(batch),
                batch.reference_date,
                ("Processamento reprocessado",),
                initial,
            )
        except _RunAbortedError as aborted:
            self._store.save_run(batch.id, aborted.run)
            raise ProcessingFailureError(batch.id) from aborted
        return self._store.save_run(batch.id, run)

    def get(self, batch_id: UUID) -> BatchRecord:
        return self._require(batch_id)

    def list_batches(self) -> tuple[BatchRecord, ...]:
        return self._store.list_batches()

    def list_findings(self, query: FindingQuery) -> tuple[FindingHit, ...]:
        selected: list[FindingHit] = []
        for batch in self._store.list_batches():
            run = batch.runs[-1]
            for item in run.findings:
                hit = FindingHit(
                    batch_id=batch.id,
                    batch_identifier=batch.identifier,
                    file_name=batch.file_name,
                    code=item.code,
                    description=item.description,
                    severity=item.severity,
                    operation_identifier=item.operation_identifier,
                    occurred_at=run.finished_at,
                )
                if _matches(hit, query):
                    selected.append(hit)
        return tuple(selected)

    def metrics(self) -> ProcessingMetrics:
        snapshots = [
            RunSnapshot(
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                operation_count=run.operation_count,
                error_operation_count=run.error_operation_count,
                inconsistency_count=run.error_count + run.warning_count,
                reprocessed=any(
                    event.action == "Processamento reprocessado" for event in run.events
                ),
            )
            for batch in self._store.list_batches()
            for run in batch.runs
        ]
        return summarize(snapshots)

    def _require(self, batch_id: UUID) -> BatchRecord:
        batch = self._store.get(batch_id)
        if batch is None:
            raise BatchNotFoundError(str(batch_id))
        return batch

    def _execute(
        self,
        operations: Sequence[Operation],
        reference_date: date,
        opening_events: tuple[str, ...],
        initial: ProcessingState,
    ) -> RunRecord:
        started_at = self._clock.now()
        state = initial.transition_to(ProcessingStatus.PROCESSING)
        events = [EventRecord(action, started_at) for action in opening_events]
        events.append(EventRecord("Processamento iniciado", started_at))
        try:
            findings = self._evaluator(operations, reference_date)
        except Exception as exc:
            finished_at = self._clock.now()
            events.append(EventRecord("Processamento finalizado", finished_at))
            run = self._run(
                state.transition_to(ProcessingStatus.FAILED),
                started_at,
                finished_at,
                events,
                (),
                len(operations),
            )
            raise _RunAbortedError(run) from exc
        finished_at = self._clock.now()
        has_error = any(item.severity is Severity.ERROR for item in findings)
        target = (
            ProcessingStatus.COMPLETED_WITH_ERRORS
            if has_error
            else ProcessingStatus.COMPLETED
        )
        reported: list[str] = []
        for finding in findings:
            if finding.code in reported:
                continue
            reported.append(finding.code)
            events.append(EventRecord(f"Regra {finding.code} executada", finished_at))
        events.append(EventRecord("Processamento finalizado", finished_at))
        return self._run(
            state.transition_to(target),
            started_at,
            finished_at,
            events,
            findings,
            len(operations),
        )

    def _batch(self, command: BatchCommand, run: RunRecord) -> BatchRecord:
        started_at = run.started_at
        return BatchRecord(
            id=uuid4(),
            identifier=command.identifier,
            file_name=command.file_name,
            reference_date=command.reference_date,
            created_at=started_at,
            operations=tuple(
                OperationRecord(item.identifier, item.amount, item.occurred_on)
                for item in command.operations
            ),
            runs=(run,),
        )

    def _run(
        self,
        state: ProcessingState,
        started_at: datetime,
        finished_at: datetime,
        events: list[EventRecord],
        findings: Sequence[Finding],
        operation_count: int,
    ) -> RunRecord:
        error_ids = {
            finding.operation_identifier
            for finding in findings
            if finding.severity is Severity.ERROR
        }
        return RunRecord(
            id=uuid4(),
            status=state.status,
            started_at=started_at,
            finished_at=finished_at,
            operation_count=operation_count,
            error_count=sum(
                1 for finding in findings if finding.severity is Severity.ERROR
            ),
            warning_count=sum(
                1 for finding in findings if finding.severity is Severity.WARNING
            ),
            error_operation_count=len(error_ids),
            findings=tuple(
                FindingRecord(
                    code=finding.code,
                    description=finding.description,
                    severity=finding.severity.value,
                    operation_identifier=finding.operation_identifier,
                )
                for finding in findings
            ),
            events=tuple(events),
        )


def _operations(batch: BatchRecord) -> tuple[Operation, ...]:
    return tuple(
        Operation(item.identifier, item.amount, item.occurred_on)
        for item in batch.operations
    )


def _matches(hit: FindingHit, query: FindingQuery) -> bool:
    if not _contains(query.batch, hit.batch_identifier, hit.file_name):
        return False
    if not _contains(query.operation, hit.operation_identifier):
        return False
    if query.code and query.code.casefold() != hit.code.casefold():
        return False
    if query.severity and query.severity != hit.severity:
        return False
    if query.since is not None and hit.occurred_at < query.since:
        return False
    return query.until is None or hit.occurred_at <= query.until


def _contains(term: str, *values: str) -> bool:
    if not term:
        return True
    folded = term.casefold()
    return any(folded in value.casefold() for value in values)
