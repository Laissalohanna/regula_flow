from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from regulaflow.domain.status import ProcessingStatus


@dataclass(frozen=True, slots=True)
class OperationRecord:
    identifier: str
    amount: Decimal
    occurred_on: date


@dataclass(frozen=True, slots=True)
class FindingHit:
    batch_id: UUID
    batch_identifier: str
    file_name: str
    code: str
    description: str
    severity: str
    operation_identifier: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class FindingRecord:
    code: str
    description: str
    severity: str
    operation_identifier: str


@dataclass(frozen=True, slots=True)
class EventRecord:
    action: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RunRecord:
    id: UUID
    status: ProcessingStatus
    started_at: datetime
    finished_at: datetime
    operation_count: int
    error_count: int
    warning_count: int
    error_operation_count: int
    findings: tuple[FindingRecord, ...]
    events: tuple[EventRecord, ...]


@dataclass(frozen=True, slots=True)
class BatchRecord:
    id: UUID
    identifier: str
    file_name: str
    reference_date: date
    created_at: datetime
    operations: tuple[OperationRecord, ...]
    runs: tuple[RunRecord, ...]

    @property
    def current_status(self) -> ProcessingStatus:
        return self.runs[-1].status
