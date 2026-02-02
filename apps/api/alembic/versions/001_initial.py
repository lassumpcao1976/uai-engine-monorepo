"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    op.create_table(
        'versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('file_tree', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('unified_diff', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_versions_id'), 'versions', ['id'], unique=False)

    op.create_table(
        'builds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED', name='buildstatus'), nullable=False),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('preview_url', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_builds_id'), 'builds', ['id'], unique=False)

    op.create_table(
        'credit_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.Enum('BUILD', 'EXPORT', 'REFUND', 'BONUS', name='credittransactiontype'), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('build_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_transactions_id'), 'credit_transactions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_credit_transactions_id'), table_name='credit_transactions')
    op.drop_table('credit_transactions')
    op.drop_index(op.f('ix_builds_id'), table_name='builds')
    op.drop_table('builds')
    op.drop_index(op.f('ix_versions_id'), table_name='versions')
    op.drop_table('versions')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
