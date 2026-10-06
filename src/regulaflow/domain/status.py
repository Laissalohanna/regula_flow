from dataclasses import dataclass
from enum import StrEnum

from regulaflow.domain.errors import InvalidStatusTransitionError


class ProcessingStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"
    REPROCESSING = "REPROCESSING"


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


@dataclass(frozen=True, slots=True)
class ProcessingState:
    """Status de um processamento. A troca sempre produz um estado novo."""

    status: ProcessingStatus

    @classmethod
    def received(cls) -> "ProcessingState":
        return cls(status=ProcessingStatus.RECEIVED)

    def transition_to(self, target: ProcessingStatus) -> "ProcessingState":
        if target not in _ALLOWED[self.status]:
            raise InvalidStatusTransitionError(self.status.value, target.value)
        return ProcessingState(status=target)
