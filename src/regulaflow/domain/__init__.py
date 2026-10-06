"""Regras de negócio puras. Esta camada não conhece banco, fila nem HTTP."""

from regulaflow.domain.errors import DomainError, InvalidStatusTransitionError
from regulaflow.domain.status import ProcessingState, ProcessingStatus

__all__ = [
    "DomainError",
    "InvalidStatusTransitionError",
    "ProcessingState",
    "ProcessingStatus",
]
