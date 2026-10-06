import pytest

from regulaflow.domain import (
    InvalidStatusTransitionError,
    ProcessingState,
    ProcessingStatus,
)

_ALLOWED: dict[ProcessingStatus, frozenset[ProcessingStatus]] = {
    ProcessingStatus.RECEIVED: frozenset({ProcessingStatus.PROCESSING}),
    ProcessingStatus.PROCESSING: frozenset(
        {
            ProcessingStatus.COMPLETED,
            ProcessingStatus.COMPLETED_WITH_ERRORS,
            ProcessingStatus.FAILED,
        }
    ),
    ProcessingStatus.COMPLETED: frozenset(),
    ProcessingStatus.COMPLETED_WITH_ERRORS: frozenset({ProcessingStatus.REPROCESSING}),
    ProcessingStatus.FAILED: frozenset({ProcessingStatus.REPROCESSING}),
    ProcessingStatus.REPROCESSING: frozenset({ProcessingStatus.PROCESSING}),
}


def test_new_processing_starts_as_received() -> None:
    assert ProcessingState.received().status is ProcessingStatus.RECEIVED


@pytest.mark.parametrize("current", list(ProcessingStatus))
@pytest.mark.parametrize("target", list(ProcessingStatus))
def test_transition_matrix(current: ProcessingStatus, target: ProcessingStatus) -> None:
    state = ProcessingState(status=current)

    if target in _ALLOWED[current]:
        assert state.transition_to(target).status is target
        return

    with pytest.raises(InvalidStatusTransitionError) as captured:
        state.transition_to(target)

    assert captured.value.current == current.value
    assert captured.value.target == target.value
