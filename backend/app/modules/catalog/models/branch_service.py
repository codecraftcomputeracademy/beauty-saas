from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class BranchService(Base):
    __tablename__ = "branch_services"

    __table_args__ = (
        ForeignKeyConstraint(
            ["branch_id", "organization_id"],
            ["branches.id", "branches.organization_id"],
            name="fk_branch_services_branch_same_org",
        ),
        ForeignKeyConstraint(
            ["service_id", "organization_id"],
            ["services.id", "services.organization_id"],
            name="fk_branch_services_service_same_org",
        ),
        UniqueConstraint(
            "organization_id",
            "branch_id",
            "service_id",
            name="uq_branch_services_branch_service",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_branch_services_id_organization",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            "branch_id",
            name="uq_branch_services_id_organization_branch",
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

    service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    duration_minutes: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    status: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
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