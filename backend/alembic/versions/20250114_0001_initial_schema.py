"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2025-01-14 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Create custom enum types only for PostgreSQL (if they don't exist)
    if dialect_name == 'postgresql':
        from sqlalchemy.dialects import postgresql
        # Check and create chat_type_enum if it doesn't exist
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE chat_type_enum AS ENUM ('private', 'group', 'channel');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        # Check and create schedule_type_enum if it doesn't exist
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE schedule_type_enum AS ENUM ('once', 'cron');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
    
    # Helper to get JSON type based on dialect
    json_type = sa.JSON() if dialect_name == 'sqlite' else sa.JSON()
    
    # Helper to get current timestamp based on dialect
    timestamp_default = sa.text("CURRENT_TIMESTAMP" if dialect_name == 'sqlite' else 'now()')
    
    # Create bots table
    op.create_table(
        'bots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False, comment='Bot type (e.g., translation, search)'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='User-defined bot name'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('config', json_type, nullable=False, server_default='{}'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bots_type'), 'bots', ['type'], unique=False)
    
    # Helper to get chat_type column based on dialect
    if dialect_name == 'postgresql':
        from sqlalchemy.dialects import postgresql
        chat_type_col = sa.Column('chat_type', postgresql.ENUM('private', 'group', 'channel', name='chat_type_enum'), nullable=True, comment='Type of chat')
    else:
        chat_type_col = sa.Column('chat_type', sa.String(length=50), nullable=True, comment='Type of chat')
    
    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('jid', sa.String(length=100), nullable=False, comment='WhatsApp JID (unique identifier)'),
        sa.Column('name', sa.String(length=255), nullable=True, comment='Chat name (group name or contact name)'),
        chat_type_col,
        sa.Column('metadata', json_type, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jid')
    )
    op.create_index(op.f('ix_chats_jid'), 'chats', ['jid'], unique=True)
    
    # Create chat_bots table
    op.create_table(
        'chat_bots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('chat_id', sa.String(length=36), nullable=False),
        sa.Column('bot_id', sa.String(length=36), nullable=False),
        sa.Column('config_override', json_type, nullable=False, server_default='{}', comment='Per-chat configuration overrides'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0', comment='Execution order (lower = earlier)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id', 'bot_id', name='uq_chat_bot')
    )
    op.create_index('ix_chat_bots_bot_id', 'chat_bots', ['bot_id'], unique=False)
    op.create_index('ix_chat_bots_chat_id', 'chat_bots', ['chat_id'], unique=False)
    
    # Create processed_messages table
    op.create_table(
        'processed_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False, comment='WhatsApp message ID'),
        sa.Column('chat_id', sa.String(length=36), nullable=True),
        sa.Column('bot_id', sa.String(length=36), nullable=True),
        sa.Column('content', sa.String(), nullable=True, comment='Original message content'),
        sa.Column('response', sa.String(), nullable=True, comment='Bot response'),
        sa.Column('metadata', json_type, nullable=False, server_default='{}'),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    op.create_index('ix_processed_messages_chat_bot', 'processed_messages', ['chat_id', 'bot_id'], unique=False)
    op.create_index('ix_processed_messages_message_id', 'processed_messages', ['message_id'], unique=False)
    op.create_index('ix_processed_messages_processed_at', 'processed_messages', ['processed_at'], unique=False)
    
    # Helper to get schedule_type column based on dialect
    if dialect_name == 'postgresql':
        from sqlalchemy.dialects import postgresql
        schedule_type_col = sa.Column('schedule_type', postgresql.ENUM('once', 'cron', name='schedule_type_enum'), nullable=False, comment='Schedule type: once or cron')
    else:
        schedule_type_col = sa.Column('schedule_type', sa.String(length=50), nullable=False, comment='Schedule type: once or cron')
    
    # Create scheduled_messages table
    op.create_table(
        'scheduled_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('chat_id', sa.String(length=36), nullable=False),
        sa.Column('message', sa.String(), nullable=False, comment='Message to send'),
        schedule_type_col,
        sa.Column('schedule_expression', sa.String(length=255), nullable=False, comment='ISO datetime or cron expression'),
        sa.Column('timezone', sa.String(length=100), nullable=False, server_default='UTC'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True, comment='Next scheduled run time'),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True, comment='Last execution time'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', json_type, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_messages_chat_id', 'scheduled_messages', ['chat_id'], unique=False)
    # Only PostgreSQL supports partial indexes
    if dialect_name == 'postgresql':
        op.create_index('ix_scheduled_messages_next_run', 'scheduled_messages', ['next_run_at'], unique=False, postgresql_where=sa.text('enabled = true'))
    else:
        op.create_index('ix_scheduled_messages_next_run', 'scheduled_messages', ['next_run_at'], unique=False)


def downgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Drop tables in reverse order
    op.drop_index('ix_scheduled_messages_next_run', table_name='scheduled_messages')
    op.drop_index('ix_scheduled_messages_chat_id', table_name='scheduled_messages')
    op.drop_table('scheduled_messages')
    
    op.drop_index('ix_processed_messages_processed_at', table_name='processed_messages')
    op.drop_index('ix_processed_messages_message_id', table_name='processed_messages')
    op.drop_index('ix_processed_messages_chat_bot', table_name='processed_messages')
    op.drop_table('processed_messages')
    
    op.drop_index('ix_chat_bots_chat_id', table_name='chat_bots')
    op.drop_index('ix_chat_bots_bot_id', table_name='chat_bots')
    op.drop_table('chat_bots')
    
    op.drop_index(op.f('ix_chats_jid'), table_name='chats')
    op.drop_table('chats')
    
    op.drop_index(op.f('ix_bots_type'), table_name='bots')
    op.drop_table('bots')
    
    # Drop enum types only for PostgreSQL
    if dialect_name == 'postgresql':
        op.execute("DROP TYPE schedule_type_enum")
        op.execute("DROP TYPE chat_type_enum")

