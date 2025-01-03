"""added EventTicketPayment model

Revision ID: 0dd192866f1b
Revises: e3a877705642
Create Date: 2024-12-20 08:51:56.344162

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0dd192866f1b'
down_revision = 'e3a877705642'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event_ticket_payments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('participant_id', sa.Integer(), nullable=True),
    sa.Column('create_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('file_url', sa.String(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['participant_id'], ['event_participants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('event_ticket_payments')
    # ### end Alembic commands ###
