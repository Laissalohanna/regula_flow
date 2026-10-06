from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from regulaflow.application.records import FindingHit
from regulaflow.application.service import BatchCommand, BatchService, FindingQuery
from regulaflow.domain.metrics import ProcessingMetrics
from regulaflow.domain.operations import Operation
from regulaflow.interfaces.schemas import (
    BatchIn,
    BatchOut,
    BatchSummaryOut,
    DashboardOut,
    FindingHitOut,
    MetricsOut,
    batch_out,
    dashboard_out,
    summary_out,
)


def create_router(service: BatchService) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> JSONResponse:
        try:
            service.ping()
        except Exception:
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return JSONResponse(content={"status": "ok"})

    @router.post("/api/lotes", status_code=201)
    def receive(payload: BatchIn) -> BatchOut:
        batch = service.receive(
            BatchCommand(
                identifier=payload.identifier,
                file_name=payload.file_name,
                reference_date=payload.reference_date,
                operations=tuple(
                    Operation(
                        item.identifier,
                        item.amount,
                        item.occurred_on,
                        item.movement_type,
                    )
                    for item in payload.operations
                ),
            )
        )
        return batch_out(batch)

    @router.get("/api/lotes")
    def list_batches() -> list[BatchSummaryOut]:
        return [summary_out(batch) for batch in service.list_batches()]

    @router.get("/api/lotes/{batch_id}")
    def get_batch(batch_id: UUID) -> BatchOut:
        return batch_out(service.get(batch_id))

    @router.post("/api/lotes/{batch_id}/reprocessamentos", status_code=201)
    def reprocess(batch_id: UUID) -> BatchOut:
        return batch_out(service.reprocess(batch_id))

    @router.get("/api/metricas")
    def metrics() -> MetricsOut:
        return _metrics_out(service.metrics())

    @router.get("/api/painel")
    def dashboard() -> DashboardOut:
        return dashboard_out(service.dashboard())

    @router.get("/api/inconsistencias")
    def findings(
        lote: str = "",
        operacao: str = "",
        regra: str = "",
        severidade: str = "",
        desde: datetime | None = None,
        ate: datetime | None = None,
    ) -> list[FindingHitOut]:
        hits = service.list_findings(
            FindingQuery(
                batch=lote,
                operation=operacao,
                code=regra,
                severity=severidade,
                since=_aware(desde),
                until=_aware(ate),
            )
        )
        return [_finding_out(item) for item in hits]

    return router


def _metrics_out(metrics: ProcessingMetrics) -> MetricsOut:
    return MetricsOut(
        total=metrics.total,
        success_rate=metrics.success_rate,
        error_rate=metrics.error_rate,
        inconsistency_rate=metrics.inconsistency_rate,
        average_seconds=metrics.average_seconds,
        failure_count=metrics.failure_count,
        record_count=metrics.record_count,
        inconsistency_count=metrics.inconsistency_count,
        reprocess_count=metrics.reprocess_count,
    )


def _finding_out(item: FindingHit) -> FindingHitOut:
    return FindingHitOut(
        batch_id=item.batch_id,
        batch_identifier=item.batch_identifier,
        file_name=item.file_name,
        code=item.code,
        description=item.description,
        severity=item.severity,
        operation_identifier=item.operation_identifier,
        occurred_at=item.occurred_at,
    )


def _aware(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)
