from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AppointmentEventType(str, Enum):
    CREATED = "CREATED"
    BOOKED = "BOOKED"
    CONFIRMED = "CONFIRMED"
    RESCHEDULED = "RESCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AppointmentEvent(Base):
    __tablename__ = "appointment_events"

    __table_args__ = (
        ForeignKeyConstraint(
            ["appointment_id", "organization_id"],
            [
                "appointments.id",
                "appointments.organization_id",
            ],
            name="fk_appointment_events_appointment",
        ),
        ForeignKeyConstraint(
            ["created_by_user_id", "organization_id"],
            [
                "users.id",
                "users.organization_id",
            ],
            name="fk_appointment_events_created_by_user",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_appointment_events_id_organization",
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

    appointment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    event_type: Mapped[AppointmentEventType] = mapped_column(
        SQLEnum(
            AppointmentEventType,
            name="appointment_event_type",
        ),
        nullable=False,
        index=True,
    )

    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    created_by_user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )