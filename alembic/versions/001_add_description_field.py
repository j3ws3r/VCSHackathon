"""Add description field to achievements table

Revision ID: 001
Revises: 
Create Date: 2025-06-07 18:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add description field to achievements table."""
    # Add description column to achievements table
    op.add_column('achievements', sa.Column('description', sa.String(), nullable=True))
    
    # Add points_value column to achievements table (if not already exists)
    # This handles the case where we manually added it before
    try:
        op.add_column('achievements', sa.Column('points_value', sa.Integer(), nullable=True))
    except Exception:
        # Column already exists, skip
        pass
    
    # Update points_value from point_value for backward compatibility
    op.execute("UPDATE achievements SET points_value = point_value WHERE points_value IS NULL")
    
    # Make points_value NOT NULL now that it has data
    op.alter_column('achievements', 'points_value', nullable=False)


def downgrade() -> None:
    """Remove description field from achievements table."""
    # Remove description column
    op.drop_column('achievements', 'description')
    
    # Remove points_value column (keep point_value for backward compatibility)
    op.drop_column('achievements', 'points_value') 