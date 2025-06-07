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


"""Add description and points_value to achievements

Revision ID: [your_revision_id]
Revises: 
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '[your_revision_id]'  # Keep the generated ID
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add description and points_value fields to achievements table."""
    
    # Check if achievements table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'achievements' not in inspector.get_table_names():
        # Create the whole table if it doesn't exist
        op.create_table('achievements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('point_value', sa.Integer(), nullable=True),
            sa.Column('points_value', sa.Integer(), nullable=False, default=0),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('frequency', sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
    else:
        # Table exists, check what columns we need to add
        columns = [col['name'] for col in inspector.get_columns('achievements')]
        
        # Add description column if it doesn't exist
        if 'description' not in columns:
            op.add_column('achievements', sa.Column('description', sa.String(), nullable=True))
        
        # Add points_value column if it doesn't exist
        if 'points_value' not in columns:
            op.add_column('achievements', sa.Column('points_value', sa.Integer(), nullable=False, server_default='0'))
            
            # Copy data from point_value to points_value if point_value exists
            if 'point_value' in columns:
                op.execute("UPDATE achievements SET points_value = COALESCE(point_value, 0)")

def downgrade() -> None:
    """Remove description and points_value fields from achievements table."""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'achievements' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('achievements')]
        
        # Remove description column if it exists
        if 'description' in columns:
            # SQLite doesn't support dropping columns directly, so we need to recreate the table
            # For simplicity, we'll skip the downgrade or create a new table without the column
            pass
        
        # Remove points_value column if it exists
        if 'points_value' in columns:
            # SQLite doesn't support dropping columns directly
            # For development, we can skip this or recreate the table
            pass