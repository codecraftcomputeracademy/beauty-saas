from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomerContactPoint(Base):
    __tablename__ = "customer_contact_points"

    __table_args__ = (
        ForeignKeyConstraint(
            ["customer_id", "organization_id"],
            [
                "customers.id",
                "customers.organization_id",
            ],
            name="fk_customer_contact_points_customer_same_org",
        ),
        ForeignKeyConstraint(
            ["contact_point_id", "organization_id"],
            [
                "contact_points.id",
                "contact_points.organization_id",
            ],
            name="fk_customer_contact_points_contact_point_same_org",
        ),
        UniqueConstraint(
            "organization_id",
            "customer_id",
            "contact_point_id",
            name="uq_customer_contact_points_customer_contact",
        ),
        Index(
            "uq_customer_contact_points_primary",
            "organization_id",
            "customer_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
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

    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    contact_point_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # receives_appointment_notifications: Mapped[bool] = mapped_column(
    #     Boolean,
    #     nullable=False,
    #     default=True,
    # )

    # receives_marketing: Mapped[bool] = mapped_column(
    #     Boolean,
    #     nullable=False,
    #     default=False,
    # )

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