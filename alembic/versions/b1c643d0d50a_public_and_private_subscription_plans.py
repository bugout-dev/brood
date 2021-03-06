"""public and private subscription plans

Revision ID: b1c643d0d50a
Revises: d994c4e6322a
Create Date: 2021-06-18 14:13:09.515612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c643d0d50a'
down_revision = 'd994c4e6322a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subscription_plans', sa.Column('public', sa.Boolean(), nullable=True))

    #Manual
    op.execute("UPDATE subscription_plans SET public = true")
    op.alter_column("subscription_plans", "public", nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscription_plans', 'public')
    # ### end Alembic commands ###
