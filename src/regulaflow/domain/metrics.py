from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from regulaflow.domain.status import ProcessingStatus

_ERROR_STATUSES = frozenset(
    {
        ProcessingStatus.FAILED,
        ProcessingStatus.COMPLETED_WITH_ERRORS,
    }
)


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    status: ProcessingStatus
    started_at: datetime
    finished_at: datetime | None
    operation_count: int
    error_operation_count: int
    inconsistency_count: int = 0
    reprocessed: bool = False


@dataclass(frozen=True, slots=True)
class ProcessingMetrics:
    total: int
    success_rate: float
    error_rate: float
    inconsistency_rate: float
    average_seconds: float
    failure_count: int
    record_count: int
    inconsistency_count: int
    reprocess_count: int


def _rate(part: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(part * 100 / total, 2)


def summarize(runs: Sequence[RunSnapshot]) -> ProcessingMetrics:
    total = len(runs)
    successes = sum(1 for run in runs if run.status is ProcessingStatus.COMPLETED)
    errors = sum(1 for run in runs if run.status in _ERROR_STATUSES)
    operations = sum(run.operation_count for run in runs)
    operations_with_errors = sum(run.error_operation_count for run in runs)
    durations = [
        (run.finished_at - run.started_at).total_seconds()
        for run in runs
        if run.finished_at is not None
    ]
    average = round(sum(durations) / len(durations), 2) if durations else 0.0
    return ProcessingMetrics(
        total=total,
        success_rate=_rate(successes, total),
        error_rate=_rate(errors, total),
        inconsistency_rate=_rate(operations_with_errors, operations),
        average_seconds=average,
        failure_count=sum(1 for run in runs if run.status is ProcessingStatus.FAILED),
        record_count=operations,
        inconsistency_count=sum(run.inconsistency_count for run in runs),
        reprocess_count=sum(1 for run in runs if run.reprocessed),
    )
