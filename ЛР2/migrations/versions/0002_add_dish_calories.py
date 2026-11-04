"""add dish calories

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dishes', sa.Column('calories', sa.Integer(), nullable=True))
    op.create_check_constraint(
        'calories_non_negative',
        'dishes',
        'calories IS NULL OR calories >= 0',
    )


def downgrade():
    op.drop_constraint('calories_non_negative', 'dishes', type_='check')
    op.drop_column('dishes', 'calories')
