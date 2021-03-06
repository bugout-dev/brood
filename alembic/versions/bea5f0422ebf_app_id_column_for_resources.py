"""App id column for resources

Revision ID: bea5f0422ebf
Revises: 02395c3b0f59
Create Date: 2021-05-25 09:00:10.890726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bea5f0422ebf'
down_revision = '02395c3b0f59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('resources', sa.Column('application_id', sa.String(), nullable=True))
    op.add_column('resources', sa.Column('external_id', sa.String(), nullable=True))
    op.create_unique_constraint(op.f('uq_resources_external_id'), 'resources', ['external_id', 'application_id'])

    # Manual part
    op.execute("UPDATE resources SET application_id = id;")
    op.execute("UPDATE resources SET external_id = external;")
    op.alter_column("resources", "application_id", nullable=False)

    op.drop_constraint('uq_resources_external', 'resources', type_='unique')
    op.drop_column('resources', 'external')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('resources', sa.Column('external', sa.VARCHAR(), autoincrement=False, nullable=True))

    # Manual part
    op.execute("UPDATE resources SET external = external_id;")

    op.create_unique_constraint('uq_resources_external', 'resources', ['external'])
    op.drop_constraint(op.f('uq_resources_external_id'), 'resources', type_='unique')
    op.drop_constraint(op.f('uq_resources_application_id'), 'resources', type_='unique')
    op.drop_column('resources', 'external_id')
    op.drop_column('resources', 'application_id')
    # ### end Alembic commands ###
