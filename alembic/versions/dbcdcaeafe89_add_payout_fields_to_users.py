"""add_payout_fields_to_users

Revision ID: dbcdcaeafe89
Revises: 
Create Date: 2026-08-23 22:13:14.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dbcdcaeafe89'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('default_bank_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('bank_account_last4', sa.String(4), nullable=True))
    op.add_column('users', sa.Column('bank_account_encrypted', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('routing_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('payout_method_verified', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('users', sa.Column('payout_verified_at', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'payout_verified_at')
    op.drop_column('users', 'payout_method_verified')
    op.drop_column('users', 'routing_number')
    op.drop_column('users', 'bank_account_encrypted')
    op.drop_column('users', 'bank_account_last4')
    op.drop_column('users', 'default_bank_name')