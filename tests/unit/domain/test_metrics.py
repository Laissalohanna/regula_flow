from datetime import UTC, datetime

from regulaflow.domain.metrics import RunSnapshot, summarize
from regulaflow.domain.status import ProcessingStatus


def _run(
    status: ProcessingStatus,
    *,
    seconds: int = 4,
    operations: int = 2,
    errors: int = 0,
    finished: bool = True,
    inconsistency_count: int = 0,
    reprocessed: bool = False,
) -> RunSnapshot:
    started = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    finished_at = None
    if finished:
        finished_at = datetime(2026, 10, 6, 12, 0, seconds, tzinfo=UTC)
    return RunSnapshot(
        status=status,
        started_at=started,
        finished_at=finished_at,
        operation_count=operations,
        error_operation_count=errors,
        inconsistency_count=inconsistency_count,
        reprocessed=reprocessed,
    )


def test_empty_summary() -> None:
    metrics = summarize([])
    assert metrics.total == 0
    assert metrics.success_rate == 0
    assert metrics.error_rate == 0
    assert metrics.inconsistency_rate == 0
    assert metrics.average_seconds == 0
    assert metrics.failure_count == 0
    assert metrics.record_count == 0
    assert metrics.inconsistency_count == 0
    assert metrics.reprocess_count == 0


def test_summary_uses_terminal_statuses_and_durations() -> None:
    metrics = summarize(
        [
            _run(
                ProcessingStatus.COMPLETED,
                seconds=4,
                operations=4,
                errors=1,
                inconsistency_count=2,
                reprocessed=True,
            ),
            _run(ProcessingStatus.FAILED, seconds=2, operations=4, errors=0),
            _run(ProcessingStatus.PROCESSING, finished=False, operations=0),
        ]
    )
    assert metrics.total == 3
    assert metrics.success_rate == 33.33
    assert metrics.error_rate == 33.33
    assert metrics.inconsistency_rate == 12.5
    assert metrics.average_seconds == 3
    assert metrics.failure_count == 1
    assert metrics.record_count == 8
    assert metrics.inconsistency_count == 2
    assert metrics.reprocess_count == 1
