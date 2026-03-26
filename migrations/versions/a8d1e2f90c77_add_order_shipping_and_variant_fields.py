"""add order shipping info and rich variant fields

Revision ID: a8d1e2f90c77
Revises: 49db47a92378
Create Date: 2026-03-26 15:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = 'a8d1e2f90c77'
down_revision = '49db47a92378'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recipient_name', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('ward', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('district', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('address_line', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('note', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('payment_method', sa.String(length=64), nullable=True))

    with op.batch_alter_table('product_variant', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('color', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('image_url', sa.String(length=256), nullable=True))


def downgrade():
    with op.batch_alter_table('product_variant', schema=None) as batch_op:
        batch_op.drop_column('image_url')
        batch_op.drop_column('color')
        batch_op.drop_column('price')
        batch_op.drop_column('description')
        batch_op.drop_column('name')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('payment_method')
        batch_op.drop_column('note')
        batch_op.drop_column('address_line')
        batch_op.drop_column('district')
        batch_op.drop_column('ward')
        batch_op.drop_column('city')
        batch_op.drop_column('phone')
        batch_op.drop_column('recipient_name')
