from uuid import uuid4

from sqlalchemy import (
    ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.models.base import Base


class AppointmentServiceResource(Base):
    __tablename__ = "appointment_service_resources"

    __table_args__ = (
        ForeignKeyConstraint(
            ["appointment_service_id", "organization_id"],
            [
                "appointment_services.id",
                "appointment_services.organization_id",
            ],
            name="fk_appointment_service_resources_service",
        ),
        ForeignKeyConstraint(
            ["resource_id", "organization_id", "branch_id"],
            [
                "resources.id",
                "resources.organization_id",
                "resources.branch_id",
            ],
            name="fk_appointment_service_resources_resource",
        ),
        ForeignKeyConstraint(
            ["branch_id", "organization_id"],
            [
                "branches.id",
                "branches.organization_id",
            ],
            name="fk_appointment_service_resources_branch",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_appointment_service_resources_id_organization",
        ),
        UniqueConstraint(
            "organization_id",
            "appointment_service_id",
            "resource_id",
            name="uq_appointment_service_resources_service_resource",
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

    appointment_service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
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