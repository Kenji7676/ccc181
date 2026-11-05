"""add tickets.served_at

Revision ID: b47d004b62e4
Revises: c9bbcb0511af
Create Date: 2026-11-05 16:44:36.921907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b47d004b62e4'
down_revision = 'c9bbcb0511af'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('served_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_check_constraint(
            'ck_tickets_served_after_created',
            'served_at IS NULL OR served_at >= created_at',
        )

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.drop_constraint('ck_tickets_served_after_created', type_='check')
        batch_op.drop_column('served_at')
        
    # ### end Alembic commands ###
