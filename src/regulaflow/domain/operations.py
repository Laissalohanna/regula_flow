from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Operation:
    identifier: str
    amount: Decimal
    occurred_on: date
