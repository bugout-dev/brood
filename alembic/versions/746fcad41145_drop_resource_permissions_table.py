"""Drop resource permissions table

Revision ID: 746fcad41145
Revises: 646fcad41144
Create Date: 2024-01-25 06:23:57.687448

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '746fcad41145'
down_revision = '646fcad41144'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###  
    op.drop_constraint('fk_resource_holder_permissions_permission_id_resource_p_4661', 'resource_holder_permissions', type_='foreignkey')
    op.drop_column('resource_holder_permissions', 'permission_id')
    op.drop_table('resource_permissions')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    return
    op.create_table('resource_permissions',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('resource_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('permission', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], name='fk_resource_permissions_resource_id_resources', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='pk_resource_permissions')
    )
    op.add_column('resource_holder_permissions', sa.Column('permission_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('fk_resource_holder_permissions_permission_id_resource_permissions', 'resource_holder_permissions', 'resource_permissions', ['permission_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###
