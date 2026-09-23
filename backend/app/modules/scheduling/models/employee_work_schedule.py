from datetime import time
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class EmployeeWorkSchedule(Base):
    __tablename__ = "employee_work_schedules"

    __table_args__ = (
        ForeignKeyConstraint(
            ["employee_id", "organization_id"],
            ["employees.id", "employees.organization_id"],
            name="fk_employee_work_schedules_employee_same_org",
        ),
        ForeignKeyConstraint(
            ["branch_id", "organization_id"],
            ["branches.id", "branches.organization_id"],
            name="fk_employee_work_schedules_branch_same_org",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_employee_work_schedules_id_organization",
        ),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_employee_work_schedules_day_of_week",
        ),
        CheckConstraint(
            "starts_at < ends_at",
            name="ck_employee_work_schedules_times",
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

    day_of_week: Mapped[int] = mapped_column(
        nullable=False,
    )

    starts_at: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    ends_at: Mapped[time] = mapped_column(
        Time,
        nullable=False,
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