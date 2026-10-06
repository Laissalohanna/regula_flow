from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from regulaflow.application.service import BatchCommand, BatchService
from regulaflow.domain.operations import MovementType, Operation

_GAPS = (2, 38, 1, 55, 3, 41, 2, 70, 4)

_REFERENCE = date(2026, 10, 1)


def _operation(
    identifier: str,
    amount: str,
    day: int,
    month: int = 10,
    movement: MovementType = MovementType.ACQUISITION,
) -> Operation:
    return Operation(identifier, Decimal(amount), date(2026, month, day), movement)


def _commands() -> tuple[BatchCommand, ...]:
    return (
        BatchCommand(
            identifier="LOTE-SP-1042",
            file_name="movimentacoes_sp.csv",
            reference_date=_REFERENCE,
            operations=(
                _operation("OP-4401", "1280.50", 2, movement=MovementType.ACQUISITION),
                _operation("OP-4402", "860.00", 3, movement=MovementType.SETTLEMENT),
                _operation("OP-4403", "240.90", 6, movement=MovementType.TRANSFER),
            ),
        ),
        BatchCommand(
            identifier="LOTE-RJ-1042",
            file_name="movimentacoes_rj.csv",
            reference_date=_REFERENCE,
            operations=(
                _operation("OP-2201", "0", 4, movement=MovementType.ACQUISITION),
                _operation("OP-2201", "90.00", 4, movement=MovementType.REDEMPTION),
                _operation("OP-2208", "430.00", 4, 11, MovementType.SETTLEMENT),
                _operation("OP-2210", "1500.00", 8, movement=MovementType.TRANSFER),
            ),
        ),
        BatchCommand(
            identifier="LOTE-MG-1042",
            file_name="movimentacoes_mg.csv",
            reference_date=_REFERENCE,
            operations=(
                _operation("OP-3301", "640.00", 18, 9, MovementType.REDEMPTION),
                _operation("OP-3302", "210.40", 19, 9, MovementType.REVERSAL),
            ),
        ),
        BatchCommand(
            identifier="LOTE-PR-1042",
            file_name="movimentacoes_pr.csv",
            reference_date=_REFERENCE,
            operations=(
                _operation("op 88", "75.00", 5, movement=MovementType.TRANSFER),
                _operation("   ", "320.00", 5, movement=MovementType.ACQUISITION),
                _operation("OP-5104", "980.00", 7, movement=MovementType.SETTLEMENT),
            ),
        ),
    )


class DemoClock:
    def __init__(self) -> None:
        self._moment = datetime(2026, 10, 6, 11, 4, tzinfo=UTC)
        self._index = 0

    def now(self) -> datetime:
        current = self._moment
        self._moment += timedelta(seconds=_GAPS[self._index % len(_GAPS)])
        self._index += 1
        return current


def load_demo(service: BatchService) -> None:
    if service.list_batches():
        return
    for command in _commands():
        service.receive(command)
    rio = next(
        batch for batch in service.list_batches() if batch.identifier == "LOTE-RJ-1042"
    )
    service.reprocess(rio.id)
