"""removed holder id from ticket payment and added it to the ticket

Revision ID: 9ddddf4be827
Revises: a5f510da307e
Create Date: 2024-12-28 11:04:30.114325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ddddf4be827'
down_revision = 'a5f510da307e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event_ticket_payments', schema=None) as batch_op:
        batch_op.drop_constraint('event_ticket_payments_holder_id_fkey', type_='foreignkey')
        batch_op.drop_column('holder_id')

    with op.batch_alter_table('event_tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('holder_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'event_participants', ['holder_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event_tickets', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('holder_id')

    with op.batch_alter_table('event_ticket_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('holder_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('event_ticket_payments_holder_id_fkey', 'event_participants', ['holder_id'], ['id'])

    # ### end Alembic commands ###