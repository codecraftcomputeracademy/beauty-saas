# from datetime import date, datetime

# from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func

# from uuid import UUID, uuid4

# from sqlalchemy import DateTime, String, Text, func
# from sqlalchemy.dialects.postgresql import UUID as PGUUID
# from sqlalchemy.orm import Mapped, mapped_column

# from app.models.base import Base

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKeyConstraint,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    __table_args__ = (
        ForeignKeyConstraint(
            ["administrator_user_id", "id"],
            ["users.id", "users.organization_id"],
            name="fk_organizations_admin_same_org",
        ),
    )
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    administrator_user_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    
    nullable=True,
    index=True,
    )

    client_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    legal_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    logo_file_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Asia/Kolkata",
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    locale: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="en-IN",
    )

    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="IN",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    validity_until: Mapped[date] = mapped_column(
    Date,
    nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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