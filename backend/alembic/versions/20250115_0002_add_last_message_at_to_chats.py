"""add_last_message_at_to_chats

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-15 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Add last_message_at column to chats table
    op.add_column('chats', sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of the last message from WhatsApp'))
    
    # Create index on last_message_at
    op.create_index('ix_chats_last_message_at', 'chats', ['last_message_at'], unique=False)


def downgrade() -> None:
    # Drop index and column
    op.drop_index('ix_chats_last_message_at', table_name='chats')
    op.drop_column('chats', 'last_message_at')

