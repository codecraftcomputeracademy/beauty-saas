from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class CustomerRelationship(Base):
    __tablename__ = "customer_relationships"

    __table_args__ = (
        ForeignKeyConstraint(
            ["customer_id", "organization_id"],
            ["customers.id", "customers.organization_id"],
            name="fk_customer_relationships_customer_same_org",
        ),
        ForeignKeyConstraint(
            ["related_customer_id", "organization_id"],
            ["customers.id", "customers.organization_id"],
            name="fk_customer_relationships_related_customer_same_org",
        ),
        ForeignKeyConstraint(
            ["relationship_type_id", "organization_id"],
            [
                "customer_relationship_types.id",
                "customer_relationship_types.organization_id",
            ],
            name="fk_customer_relationships_type_same_org",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_customer_relationships_id_organization",
        ),
        CheckConstraint(
            "customer_id <> related_customer_id",
            name="ck_customer_relationships_no_self",
        ),
        Index(
            "uq_customer_relationships_active",
            "organization_id",
            "customer_id",
            "related_customer_id",
            "relationship_type_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
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

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    related_customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    relationship_type_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
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