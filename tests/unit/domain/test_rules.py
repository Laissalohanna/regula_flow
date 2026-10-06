from datetime import date
from decimal import Decimal

from regulaflow.domain.operations import Operation
from regulaflow.domain.rules import Severity, evaluate

REFERENCE = date(2026, 10, 1)


def _operation(
    identifier: str = "OP1",
    amount: str = "10.00",
    occurred_on: date = date(2026, 10, 6),
) -> Operation:
    return Operation(
        identifier=identifier,
        amount=Decimal(amount),
        occurred_on=occurred_on,
    )


def _codes(operations: list[Operation]) -> list[tuple[str, Severity]]:
    return [
        (finding.code, finding.severity) for finding in evaluate(operations, REFERENCE)
    ]


def test_valid_operation_has_no_findings() -> None:
    assert evaluate([_operation()], REFERENCE) == ()


def test_blank_identifier_is_val001() -> None:
    assert _codes([_operation(identifier="  ")]) == [("VAL001", Severity.ERROR)]


def test_invalid_identifier_is_val006() -> None:
    assert _codes([_operation(identifier="op 1")]) == [("VAL006", Severity.ERROR)]


def test_duplicate_identifier_flags_the_second_operation() -> None:
    findings = evaluate([_operation(), _operation()], REFERENCE)
    assert [(item.code, item.operation_identifier) for item in findings] == [
        ("VAL004", "OP1")
    ]


def test_too_many_decimal_places_is_val002() -> None:
    assert _codes([_operation(amount="1.239")]) == [("VAL002", Severity.ERROR)]


def test_non_finite_amount_is_val002() -> None:
    assert _codes([_operation(amount="NaN")]) == [("VAL002", Severity.ERROR)]


def test_amount_must_be_positive() -> None:
    assert _codes([_operation(amount="0")]) == [("VAL005", Severity.ERROR)]
    assert _codes([_operation(amount="-3")]) == [("VAL005", Severity.ERROR)]


def test_date_outside_reference_month_is_warning() -> None:
    assert _codes([_operation(occurred_on=date(2026, 11, 1))]) == [
        ("VAL003", Severity.WARNING)
    ]


def test_operation_can_carry_error_and_warning() -> None:
    assert _codes([_operation(amount="-1", occurred_on=date(2025, 10, 2))]) == [
        ("VAL005", Severity.ERROR),
        ("VAL003", Severity.WARNING),
    ]
