"""Add organization hostname

Revision ID: ad1bea6e0034
Revises: 8c92ed5765e9
Create Date: 2026-10-02 17:11:26.279570

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ad1bea6e0034"
down_revision: Union[str, Sequence[str], None] = "8c92ed5765e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Add the column temporarily as nullable so existing
    # organizations can be populated.
    op.add_column(
        "organizations",
        sa.Column(
            "hostname",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # 2. Populate the hostname for the existing development organization.
    op.execute(
        """
        UPDATE organizations
        SET hostname = 'test-beauty.localhost'
        WHERE id = '5d3602f7-042b-4422-a030-5360569b68e5'
        """
    )

    # 3. Make hostname mandatory after existing data is populated.
    op.alter_column(
        "organizations",
        "hostname",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # 4. Enforce hostname uniqueness.
    op.create_unique_constraint(
        "uq_organizations_hostname",
        "organizations",
        ["hostname"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_organizations_hostname",
        "organizations",
        type_="unique",
    )

    op.drop_column(
        "organizations",
        "hostname",
    )