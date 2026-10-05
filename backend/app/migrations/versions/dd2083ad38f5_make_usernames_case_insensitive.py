"""Make usernames case insensitive

Revision ID: dd2083ad38f5
Revises: ad1bea6e0034
Create Date: 2026-10-04 21:45:47.410423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd2083ad38f5'
down_revision: Union[str, Sequence[str], None] = 'ad1bea6e0034'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make usernames case-insensitive within an organization."""

    # Remove the existing case-sensitive uniqueness rule.
    op.drop_constraint(
        "uq_users_organization_username",
        "users",
        type_="unique",
    )

    # Enforce case-insensitive username uniqueness per organization.
    op.create_index(
        "uq_users_organization_username_lower",
        "users",
        [
            "organization_id",
            sa.text("lower(username)"),
        ],
        unique=True,
    )


def downgrade() -> None:
    """Restore case-sensitive username uniqueness."""

    op.drop_index(
        "uq_users_organization_username_lower",
        table_name="users",
    )

    op.create_unique_constraint(
        "uq_users_organization_username",
        "users",
        [
            "organization_id",
            "username",
        ],
    )
