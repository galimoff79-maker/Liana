"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('avatar_path', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    # Sessions
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', sa.String(255), unique=True, nullable=False),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_active', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('revoked', sa.Boolean(), default=False),
    )
    op.create_index('ix_sessions_jti', 'sessions', ['jti'])

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('sender_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('text', sa.Text(), default=''),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('edited', sa.Boolean(), default=False),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_for_all', sa.Boolean(), default=False),
        sa.Column('reply_to', sa.String(), sa.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reactions', sa.JSON(), default=dict),
        sa.Column('pinned', sa.Boolean(), default=False),
        sa.Column('voice_duration', sa.Integer(), nullable=True),
        sa.Column('read_by', sa.JSON(), default=list),
        sa.Column('delivered_to', sa.JSON(), default=list),
    )
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'])
    op.create_index('ix_messages_deleted_for_all', 'messages', ['deleted_for_all'])

    # Message Deletions
    op.create_table(
        'message_deletions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('message_id', sa.String(), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_message_deletions_message_id', 'message_deletions', ['message_id'])
    op.create_index('ix_message_deletions_user_id', 'message_deletions', ['user_id'])

    # Attachments
    op.create_table(
        'attachments',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('message_id', sa.String(), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('thumbnail_path', sa.String(1000), nullable=True),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_attachments_message_id', 'attachments', ['message_id'])
    op.create_index('ix_attachments_created_at', 'attachments', ['created_at'])
    op.create_index('ix_attachments_expires_at', 'attachments', ['expires_at'])

    # Invites
    op.create_table(
        'invites',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('used', sa.Boolean(), default=False),
        sa.Column('used_by', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_invites_code', 'invites', ['code'])

    # Push Subscriptions
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.String(500), nullable=False),
        sa.Column('auth', sa.String(500), nullable=False),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_push_subscriptions_user_id', 'push_subscriptions', ['user_id'])

def downgrade() -> None:
    op.drop_table('push_subscriptions')
    op.drop_table('invites')
    op.drop_table('attachments')
    op.drop_table('message_deletions')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('users')
