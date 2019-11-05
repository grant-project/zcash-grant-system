"""empty message

Revision ID: c2ccca4545b0
Revises: 4d7a02cc2076
Create Date: 2019-11-01 15:59:52.132426

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2ccca4545b0'
down_revision = '4d7a02cc2076'
branch_labels = None
depends_on = None


def upgrade():
# ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ccr_liker')
    # ### end Alembic commands ###


def downgrade():
# ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ccr_liker',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ccr_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['ccr_id'], ['ccr.id'], name='ccr_liker_ccr_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='ccr_liker_user_id_fkey')
    )
    # ### end Alembic commands ###