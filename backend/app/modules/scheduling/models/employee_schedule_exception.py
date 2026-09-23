from datetime import date, time
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKeyConstraint,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class EmployeeScheduleExceptionType(str, Enum):
    OFF = "OFF"
    WORK = "WORK"


class EmployeeScheduleException(Base):
    __tablename__ = "employee_schedule_exceptions"

    __table_args__ = (
        ForeignKeyConstraint(
            ["employee_id", "organization_id"],
            ["employees.id", "employees.organization_id"],
            name="fk_employee_schedule_exceptions_employee_same_org",
        ),
        ForeignKeyConstraint(
            ["branch_id", "organization_id"],
            ["branches.id", "branches.organization_id"],
            name="fk_employee_schedule_exceptions_branch_same_org",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_employee_schedule_exceptions_id_organization",
        ),
       CheckConstraint(
            "(exception_type = 'OFF' AND starts_at IS NULL AND ends_at IS NULL)"
            " OR "
            "(exception_type = 'OFF' AND starts_at IS NOT NULL "
            "AND ends_at IS NOT NULL AND starts_at < ends_at)"
        " OR "
        "(exception_type = 'WORK' AND starts_at IS NOT NULL "
        "AND ends_at IS NOT NULL AND starts_at < ends_at)",
        name="ck_employee_schedule_exceptions_type_times",
),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    branch_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    exception_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    exception_type: Mapped[EmployeeScheduleExceptionType] = mapped_column(
        SQLEnum(
            EmployeeScheduleExceptionType,
            name="employee_schedule_exception_type",
        ),
        nullable=False,
    )

    starts_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    ends_at: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    