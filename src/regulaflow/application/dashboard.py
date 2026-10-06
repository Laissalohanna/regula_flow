from collections.abc import Sequence
from dataclasses import dataclass

from regulaflow.application.records import BatchRecord
from regulaflow.domain.metrics import ProcessingMetrics
from regulaflow.domain.operations import MovementType
from regulaflow.domain.status import ProcessingStatus

_STAGES = (
    ProcessingStatus.COMPLETED,
    ProcessingStatus.COMPLETED_WITH_ERRORS,
    ProcessingStatus.FAILED,
)
_NO_EXTENSION = "sem_extensao"


@dataclass(frozen=True, slots=True)
class ChartSlice:
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    success_rate: float
    error_rate: float
    average_seconds: float
    reprocess_count: int
    failure_count: int
    file_types: tuple[ChartSlice, ...]
    stages: tuple[ChartSlice, ...]
    movements: tuple[ChartSlice, ...]


def compose_dashboard(
    batches: Sequence[BatchRecord],
    metrics: ProcessingMetrics,
) -> DashboardSnapshot:
    return DashboardSnapshot(
        success_rate=metrics.success_rate,
        error_rate=metrics.error_rate,
        average_seconds=metrics.average_seconds,
        reprocess_count=metrics.reprocess_count,
        failure_count=metrics.failure_count,
        file_types=_file_types(batches),
        stages=_stages(batches),
        movements=_movements(batches),
    )


def _file_types(batches: Sequence[BatchRecord]) -> tuple[ChartSlice, ...]:
    counts: dict[str, int] = {}
    for batch in batches:
        kind = _extension(batch.file_name)
        counts[kind] = counts.get(kind, 0) + 1
    return tuple(ChartSlice(label, count) for label, count in sorted(counts.items()))


def _stages(batches: Sequence[BatchRecord]) -> tuple[ChartSlice, ...]:
    counts = {status.value: 0 for status in _STAGES}
    for batch in batches:
        counts[batch.current_status.value] += 1
    return tuple(ChartSlice(label, count) for label, count in counts.items())


def _movements(batches: Sequence[BatchRecord]) -> tuple[ChartSlice, ...]:
    counts = {kind.value: 0 for kind in MovementType}
    for batch in batches:
        for operation in batch.operations:
            counts[operation.movement_type] += 1
    return tuple(ChartSlice(label, counts[label]) for label in counts)


def _extension(name: str) -> str:
    if "." not in name:
        return _NO_EXTENSION
    suffix = name.rsplit(".", 1)[-1].lower()
    if suffix == "":
        return _NO_EXTENSION
    return suffix
