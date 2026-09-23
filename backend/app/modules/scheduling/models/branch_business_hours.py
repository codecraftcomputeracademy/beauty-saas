from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import time

from app.models.base import Base


class BranchBusinessHours(Base):
    __tablename__ = "branch_business_hours"

    __table_args__ = (
        ForeignKeyConstraint(
            ["branch_id", "organization_id"],
            ["branches.id", "branches.organization_id"],
            name="fk_branch_business_hours_branch_same_org",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_branch_business_hours_id_organization",
        ),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_branch_business_hours_day_of_week",
        ),
        CheckConstraint(
            "(is_closed = true AND opens_at IS NULL AND closes_at IS NULL)"
            " OR "
            "(is_closed = false AND opens_at IS NOT NULL "
            "AND closes_at IS NOT NULL AND opens_at < closes_at)",
            name="ck_branch_business_hours_times",
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

    day_of_week: Mapped[int] = mapped_column(
        nullable=False,
    )

    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    opens_at: Mapped[time | None]
    closes_at: Mapped[time | None]

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