from dataclasses import replace
from uuid import UUID

from regulaflow.application.records import BatchRecord, RunRecord
from regulaflow.domain.errors import BatchNotFoundError


class MemoryBatchStore:
    def __init__(self) -> None:
        self.items: dict[UUID, BatchRecord] = {}

    def ping(self) -> None:
        return None

    def get_by_identifier(self, identifier: str) -> BatchRecord | None:
        for batch in self.items.values():
            if batch.identifier == identifier:
                return batch
        return None

    def get(self, batch_id: UUID) -> BatchRecord | None:
        return self.items.get(batch_id)

    def add(self, batch: BatchRecord) -> None:
        self.items[batch.id] = batch

    def save_run(self, batch_id: UUID, run: RunRecord) -> BatchRecord:
        current = self.items.get(batch_id)
        if current is None:
            raise BatchNotFoundError(str(batch_id))
        updated = replace(current, runs=(*current.runs, run))
        self.items[batch_id] = updated
        return updated

    def list_batches(self) -> tuple[BatchRecord, ...]:
        ordered = sorted(
            self.items.values(),
            key=lambda batch: batch.created_at,
            reverse=True,
        )
        return tuple(ordered)
