from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class MovementType(StrEnum):
    ACQUISITION = "ACQUISITION"
    SETTLEMENT = "SETTLEMENT"
    TRANSFER = "TRANSFER"
    REDEMPTION = "REDEMPTION"
    REVERSAL = "REVERSAL"


@dataclass(frozen=True, slots=True)
class Operation:
    identifier: str
    amount: Decimal
    occurred_on: date
    movement_type: MovementType = MovementType.ACQUISITION
