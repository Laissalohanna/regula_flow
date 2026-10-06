from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BatchRow(Base):
    __tablename__ = "batches"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    identifier: Mapped[str] = mapped_column(String(64), unique=True)
    file_name: Mapped[str] = mapped_column(String(255))
    reference_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    operations: Mapped[list["OperationRow"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="OperationRow.position",
    )
    runs: Mapped[list["RunRow"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="RunRow.started_at",
    )


class OperationRow(Base):
    __tablename__ = "operations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"))
    position: Mapped[int]
    identifier: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    occurred_on: Mapped[date] = mapped_column(Date)
    batch: Mapped[BatchRow] = relationship(back_populates="operations")


class RunRow(Base):
    __tablename__ = "processing_runs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    operation_count: Mapped[int]
    error_count: Mapped[int]
    warning_count: Mapped[int]
    error_operation_count: Mapped[int]
    batch: Mapped[BatchRow] = relationship(back_populates="runs")
    findings: Mapped[list["FindingRow"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="FindingRow.position",
    )
    events: Mapped[list["EventRow"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EventRow.position",
    )


class FindingRow(Base):
    __tablename__ = "findings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="CASCADE")
    )
    position: Mapped[int]
    code: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(16))
    operation_identifier: Mapped[str] = mapped_column(String(64))
    run: Mapped[RunRow] = relationship(back_populates="findings")


class EventRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="CASCADE")
    )
    position: Mapped[int]
    action: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    run: Mapped[RunRow] = relationship(back_populates="events")
