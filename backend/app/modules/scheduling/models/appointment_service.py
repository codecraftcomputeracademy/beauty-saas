from decimal import Decimal
from uuid import uuid4
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AppointmentService(Base):
    __tablename__ = "appointment_services"

    __table_args__ = (
        ForeignKeyConstraint(
            ["appointment_id", "organization_id"],
            ["appointments.id", "appointments.organization_id"],
            name="fk_appointment_services_appointment",
        ),
        ForeignKeyConstraint(
            ["branch_service_id", "organization_id", "branch_id"],
            [
                "branch_services.id",
                "branch_services.organization_id",
                "branch_services.branch_id",
            ],
            name="fk_appointment_services_branch_service",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_appointment_services_id_organization",
        ),
        CheckConstraint(
          "quantity > 0",
           name="ck_appointment_services_quantity",
        ),
        CheckConstraint(
            "duration_minutes > 0",
            name="ck_appointment_services_duration",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_appointment_services_unit_price",
        ),
        CheckConstraint(
            "scheduled_start < scheduled_end",
            name="ck_appointment_services_schedule_times",
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

    appointment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    branch_service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
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