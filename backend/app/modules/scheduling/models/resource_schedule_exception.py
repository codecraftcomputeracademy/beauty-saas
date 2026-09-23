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


class ResourceScheduleExceptionType(str, Enum):
    OFF = "OFF"
    WORK = "WORK"


class ResourceScheduleException(Base):
    __tablename__ = "resource_schedule_exceptions"

    __table_args__ = (
        ForeignKeyConstraint(
            ["resource_id", "organization_id", "branch_id"],
            [
                "resources.id",
                "resources.organization_id",
                "resources.branch_id",
            ],
            name="fk_rse_resource",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_resource_schedule_exceptions_id_organization",
        ),
        CheckConstraint(
            "(exception_type = 'OFF' AND starts_at IS NULL AND ends_at IS NULL)"
            " OR "
            "(exception_type = 'OFF' AND starts_at IS NOT NULL "
            "AND ends_at IS NOT NULL AND starts_at < ends_at)"
            " OR "
            "(exception_type = 'WORK' AND starts_at IS NOT NULL "
            "AND ends_at IS NOT NULL AND starts_at < ends_at)",
            name="ck_rse_type_times",
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

    branch_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    exception_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    exception_type: Mapped[ResourceScheduleExceptionType] = mapped_column(
        SQLEnum(
            ResourceScheduleExceptionType,
            name="resource_schedule_exception_type",
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