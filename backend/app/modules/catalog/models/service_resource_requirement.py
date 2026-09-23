from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class ServiceResourceRequirement(Base):
    __tablename__ = "service_resource_requirements"

    __table_args__ = (
        ForeignKeyConstraint(
            ["service_id", "organization_id"],
            ["services.id", "services.organization_id"],
            name="fk_service_resource_requirements_service_same_org",
        ),
        ForeignKeyConstraint(
            ["resource_id", "organization_id"],
            ["resources.id", "resources.organization_id"],
            name="fk_service_resource_requirements_resource_same_org",
        ),
        UniqueConstraint(
            "organization_id",
            "service_id",
            "resource_id",
            name="uq_service_resource_requirements_service_resource",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_service_resource_requirements_id_organization",
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

    service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    required_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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