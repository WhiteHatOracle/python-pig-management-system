"""Add verification_expiry column in user

Revision ID: 75741ba38d69
Revises: 282c154c05ad
Create Date: 2025-08-13 23:45:47.335250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75741ba38d69'
down_revision = '282c154c05ad'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column directly (SQLite supports this)
    op.add_column('user', sa.Column('verification_expiry', sa.DateTime(), nullable=True))

    # Change verification_token column type
    op.alter_column(
        'user',
        'verification_token',
        existing_type=sa.TEXT(),
        type_=sa.String(length=128),
        existing_nullable=True
    )


def downgrade():
    # Revert type change
    op.alter_column(
        'user',
        'verification_token',
        existing_type=sa.String(length=128),
        type_=sa.TEXT(),
        existing_nullable=True
    )

    # Remove the column
    op.drop_column('user', 'verification_expiry')
