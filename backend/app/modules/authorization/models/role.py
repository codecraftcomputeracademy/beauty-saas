from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    Index,
    text
    )


from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    __table_args__ = (
    Index(
        "uq_roles_system_code",
        "code",
        unique=True,
        postgresql_where=text(
            "organization_id IS NULL"
        ),
    ),
    Index(
        "uq_roles_organization_code",
        "organization_id",
        "code",
        unique=True,
        postgresql_where=text(
            "organization_id IS NOT NULL"
        ),
    ),
    Index(
        "uq_roles_organization_name",
        "organization_id",
        "name",
        unique=True,
        postgresql_where=text(
            "organization_id IS NOT NULL"
        ),
    ),
)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    role_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SYSTEM",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
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