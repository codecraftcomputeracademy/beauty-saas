"""add appointment service schedule times

Revision ID: 97577af73471
Revises: b2ee3d674814
Create Date: 2026-09-21 19:30:27.842345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97577af73471'
down_revision: Union[str, Sequence[str], None] = 'b2ee3d674814'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "appointment_services",
        sa.Column(
            "scheduled_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.add_column(
        "appointment_services",
        sa.Column(
            "scheduled_end",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_check_constraint(
        "ck_appointment_services_schedule_times",
        "appointment_services",
        "scheduled_start < scheduled_end",
    )

    op.create_index(
        op.f("ix_appointment_services_scheduled_end"),
        "appointment_services",
        ["scheduled_end"],
        unique=False,
    )

    op.create_index(
        op.f("ix_appointment_services_scheduled_start"),
        "appointment_services",
        ["scheduled_start"],
        unique=False,
    )

def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_appointment_services_scheduled_start"),
        table_name="appointment_services",
    )

    op.drop_index(
        op.f("ix_appointment_services_scheduled_end"),
        table_name="appointment_services",
    )

    op.drop_constraint(
        "ck_appointment_services_schedule_times",
        "appointment_services",
        type_="check",
    )

    op.drop_column(
        "appointment_services",
        "scheduled_end",
    )

    op.drop_column(
        "appointment_services",
        "scheduled_start",
    )