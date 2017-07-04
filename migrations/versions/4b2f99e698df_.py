"""empty message

Revision ID: 4b2f99e698df
Revises: 
Create Date: 2017-07-04 17:40:30.483208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b2f99e698df'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('role_name', sa.String(length=32), nullable=True),
    sa.Column('role_default', sa.Boolean(), nullable=True),
    sa.Column('role_permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('role_id'),
    sa.UniqueConstraint('role_name')
    )
    op.create_index(op.f('ix_roles_role_default'), 'roles', ['role_default'], unique=False)
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('user_name', sa.String(length=64), nullable=True),
    sa.Column('user_email', sa.String(length=64), nullable=True),
    sa.Column('user_password_hash', sa.String(length=128), nullable=True),
    sa.Column('user_confirmed', sa.Boolean(), nullable=True),
    sa.Column('user_location', sa.String(length=64), nullable=True),
    sa.Column('user_about_me', sa.String(length=64), nullable=True),
    sa.Column('user_member_since', sa.DateTime(), nullable=True),
    sa.Column('user_last_seen', sa.DateTime(), nullable=True),
    sa.Column('user_avatar_hash', sa.String(length=128), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('user_avatar_hash')
    )
    op.create_index(op.f('ix_users_user_email'), 'users', ['user_email'], unique=True)
    op.create_index(op.f('ix_users_user_name'), 'users', ['user_name'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_user_name'), table_name='users')
    op.drop_index(op.f('ix_users_user_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_roles_role_default'), table_name='roles')
    op.drop_table('roles')
    # ### end Alembic commands ###