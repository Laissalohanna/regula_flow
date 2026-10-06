from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_movement"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "operations",
        sa.Column(
            "movement_type",
            sa.String(32),
            nullable=False,
            server_default="ACQUISITION",
        ),
    )


def downgrade() -> None:
    op.drop_column("operations", "movement_type")
