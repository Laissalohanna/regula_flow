from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from regulaflow.application.records import BatchRecord


class OperationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(max_length=64)
    amount: Decimal
    occurred_on: date


class BatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    reference_date: date
    operations: list[OperationIn] = Field(min_length=1)


class FindingOut(BaseModel):
    code: str
    description: str
    severity: str
    operation_identifier: str


class EventOut(BaseModel):
    action: str
    created_at: datetime


class RunOut(BaseModel):
    id: UUID
    status: str
    started_at: datetime
    finished_at: datetime
    operation_count: int
    error_count: int
    warning_count: int
    findings: list[FindingOut]
    events: list[EventOut]


class OperationOut(BaseModel):
    identifier: str
    amount: Decimal
    occurred_on: date


class BatchOut(BaseModel):
    id: UUID
    identifier: str
    file_name: str
    reference_date: date
    created_at: datetime
    status: str
    operations: list[OperationOut]
    runs: list[RunOut]


class BatchSummaryOut(BaseModel):
    id: UUID
    identifier: str
    file_name: str
    reference_date: date
    created_at: datetime
    status: str
    operation_count: int
    error_count: int
    warning_count: int


class MetricsOut(BaseModel):
    total: int
    success_rate: float
    error_rate: float
    inconsistency_rate: float
    average_seconds: float
    failure_count: int
    record_count: int
    inconsistency_count: int
    reprocess_count: int


class FindingHitOut(BaseModel):
    batch_id: UUID
    batch_identifier: str
    file_name: str
    code: str
    description: str
    severity: str
    operation_identifier: str
    occurred_at: datetime


def batch_out(batch: BatchRecord) -> BatchOut:
    return BatchOut(
        id=batch.id,
        identifier=batch.identifier,
        file_name=batch.file_name,
        reference_date=batch.reference_date,
        created_at=batch.created_at,
        status=batch.current_status.value,
        operations=[
            OperationOut(
                identifier=item.identifier,
                amount=item.amount,
                occurred_on=item.occurred_on,
            )
            for item in batch.operations
        ],
        runs=[
            RunOut(
                id=run.id,
                status=run.status.value,
                started_at=run.started_at,
                finished_at=run.finished_at,
                operation_count=run.operation_count,
                error_count=run.error_count,
                warning_count=run.warning_count,
                findings=[
                    FindingOut(
                        code=item.code,
                        description=item.description,
                        severity=item.severity,
                        operation_identifier=item.operation_identifier,
                    )
                    for item in run.findings
                ],
                events=[
                    EventOut(action=item.action, created_at=item.created_at)
                    for item in run.events
                ],
            )
            for run in batch.runs
        ],
    )


def summary_out(batch: BatchRecord) -> BatchSummaryOut:
    run = batch.runs[-1]
    return BatchSummaryOut(
        id=batch.id,
        identifier=batch.identifier,
        file_name=batch.file_name,
        reference_date=batch.reference_date,
        created_at=batch.created_at,
        status=run.status.value,
        operation_count=run.operation_count,
        error_count=run.error_count,
        warning_count=run.warning_count,
    )
