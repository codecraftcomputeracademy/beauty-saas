from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class BranchServiceResourceRequirement(Base):
    __tablename__ = "branch_service_resource_requirements"

    __table_args__ = (
        ForeignKeyConstraint(
            [
                "branch_service_id",
                "organization_id",
                "branch_id",
            ],
            [
                "branch_services.id",
                "branch_services.organization_id",
                "branch_services.branch_id",
            ],
            name="fk_bsr_requirements_branch_service",
        ),
        ForeignKeyConstraint(
            [
                "resource_id",
                "organization_id",
                "branch_id",
            ],
            [
                "resources.id",
                "resources.organization_id",
                "resources.branch_id",
            ],
            name="fk_bsr_requirements_resource",
        ),
        UniqueConstraint(
            "organization_id",
            "branch_id",
            "branch_service_id",
            "resource_id",
            name="uq_branch_service_resource_requirements_service_resource",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_branch_service_resource_requirements_id_organization",
        ),
        CheckConstraint(
           "required_count > 0",
            name="ck_branch_service_resource_requirements_required_count",
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

    branch_service_id: Mapped[UUID] = mapped_column(
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