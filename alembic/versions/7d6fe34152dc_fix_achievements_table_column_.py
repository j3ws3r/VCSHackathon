"""Fix achievements table column consistency

Revision ID: 7d6fe34152dc
Revises: [your_revision_id]
Create Date: 2025-06-07 20:20:27.582417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d6fe34152dc'
down_revision: Union[str, None] = '[your_revision_id]'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
