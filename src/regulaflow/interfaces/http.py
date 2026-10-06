from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from regulaflow.application.service import BatchCommand, BatchService
from regulaflow.domain.metrics import ProcessingMetrics
from regulaflow.domain.operations import Operation
from regulaflow.interfaces.schemas import (
    BatchIn,
    BatchOut,
    BatchSummaryOut,
    MetricsOut,
    batch_out,
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
                    Operation(item.identifier, item.amount, item.occurred_on)
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

    return router


def _metrics_out(metrics: ProcessingMetrics) -> MetricsOut:
    return MetricsOut(
        total=metrics.total,
        success_rate=metrics.success_rate,
        error_rate=metrics.error_rate,
        inconsistency_rate=metrics.inconsistency_rate,
        average_seconds=metrics.average_seconds,
    )
