"""added walkin payment field

Revision ID: e808b8e45923
Revises: 2111df7044ac
Create Date: 2025-01-07 18:00:51.030451

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e808b8e45923'
down_revision = '2111df7044ac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event_ticket_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('walkin', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event_ticket_payments', schema=None) as batch_op:
        batch_op.drop_column('walkin')

    # ### end Alembic commands ###
