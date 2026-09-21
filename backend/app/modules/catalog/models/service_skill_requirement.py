from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ServiceSkillRequirement(Base):
    __tablename__ = "service_skill_requirements"

    __table_args__ = (
        ForeignKeyConstraint(
            ["service_id", "organization_id"],
            [
                "services.id",
                "services.organization_id",
            ],
            name="fk_service_skill_requirements_service_same_org",
        ),
        ForeignKeyConstraint(
            ["skill_id", "organization_id"],
            [
                "skills.id",
                "skills.organization_id",
            ],
            name="fk_service_skill_requirements_skill_same_org",
        ),
        UniqueConstraint(
            "organization_id",
            "service_id",
            "skill_id",
            name="uq_service_skill_requirements_service_skill",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    service_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    required_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )