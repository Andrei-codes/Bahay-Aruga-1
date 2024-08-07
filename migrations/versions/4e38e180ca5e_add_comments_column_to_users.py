"""Add comments column to Users

Revision ID: 4e38e180ca5e
Revises: 76a86a2a134b
Create Date: 2024-07-16 01:44:03.835511

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e38e180ca5e'
down_revision = '76a86a2a134b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medicine', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=False,
               autoincrement=True)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('comments', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('comments')

    with op.batch_alter_table('medicine', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=True,
               autoincrement=True)

    # ### end Alembic commands ###
