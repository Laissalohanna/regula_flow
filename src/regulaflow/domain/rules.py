import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from regulaflow.domain.operations import Operation

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    description: str
    severity: Severity
    operation_identifier: str


@dataclass(slots=True)
class RuleContext:
    reference_date: date
    seen: set[str]


class Rule(Protocol):
    code: str

    def check(self, operation: Operation, context: RuleContext) -> Finding | None: ...


def _invalid_amount(amount: Decimal) -> bool:
    if not amount.is_finite():
        return True
    return amount != amount.quantize(Decimal("0.01"))


class RequiredIdentifierRule:
    code = "VAL001"

    def check(self, operation: Operation, _context: RuleContext) -> Finding | None:
        if operation.identifier.strip():
            return None
        return Finding(
            self.code,
            "Campo obrigatório ausente.",
            Severity.ERROR,
            operation.identifier,
        )


class IdentifierFormatRule:
    code = "VAL006"

    def check(self, operation: Operation, _context: RuleContext) -> Finding | None:
        identifier = operation.identifier.strip()
        if not identifier or _IDENTIFIER.fullmatch(identifier):
            return None
        return Finding(
            self.code,
            "Identificador inválido.",
            Severity.ERROR,
            operation.identifier,
        )


class DuplicateOperationRule:
    code = "VAL004"

    def check(self, operation: Operation, context: RuleContext) -> Finding | None:
        identifier = operation.identifier.strip()
        if not identifier or _IDENTIFIER.fullmatch(identifier) is None:
            return None
        if identifier in context.seen:
            return Finding(
                self.code,
                "Operação duplicada.",
                Severity.ERROR,
                operation.identifier,
            )
        context.seen.add(identifier)
        return None


class AmountScaleRule:
    code = "VAL002"

    def check(self, operation: Operation, _context: RuleContext) -> Finding | None:
        if not _invalid_amount(operation.amount):
            return None
        return Finding(
            self.code,
            "Valor inválido.",
            Severity.ERROR,
            operation.identifier,
        )


class PositiveAmountRule:
    code = "VAL005"

    def check(self, operation: Operation, _context: RuleContext) -> Finding | None:
        if _invalid_amount(operation.amount) or operation.amount > 0:
            return None
        return Finding(
            self.code,
            "Valor deve ser maior que zero.",
            Severity.ERROR,
            operation.identifier,
        )


class ReferencePeriodRule:
    code = "VAL003"

    def check(self, operation: Operation, context: RuleContext) -> Finding | None:
        same_month = (
            operation.occurred_on.year == context.reference_date.year
            and operation.occurred_on.month == context.reference_date.month
        )
        if same_month:
            return None
        return Finding(
            self.code,
            "Data fora do período permitido.",
            Severity.WARNING,
            operation.identifier,
        )


RULES: tuple[Rule, ...] = (
    RequiredIdentifierRule(),
    IdentifierFormatRule(),
    DuplicateOperationRule(),
    AmountScaleRule(),
    PositiveAmountRule(),
    ReferencePeriodRule(),
)


def evaluate(
    operations: Sequence[Operation],
    reference_date: date,
) -> tuple[Finding, ...]:
    context = RuleContext(reference_date=reference_date, seen=set())
    findings: list[Finding] = []
    for operation in operations:
        for rule in RULES:
            finding = rule.check(operation, context)
            if finding is not None:
                findings.append(finding)
    return tuple(findings)
