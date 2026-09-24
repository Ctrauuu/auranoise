"""users and settings

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("timezone", sa.String(80), server_default="UTC", nullable=False),
        sa.Column("theme", sa.String(10), server_default="system", nullable=False),
        sa.Column("autosave_seconds", sa.Integer(), server_default="3", nullable=False),
        sa.Column("markdown_view", sa.String(10), server_default="single", nullable=False),
        sa.Column("show_active_goals", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("show_tasks_due_today", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("trash_retention_days", sa.Integer(), server_default="30", nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("theme IN ('system', 'light', 'dark')", name="ck_user_settings_theme"),
        sa.CheckConstraint("markdown_view IN ('single', 'split')", name="ck_user_settings_markdown_view"),
        sa.CheckConstraint("autosave_seconds BETWEEN 2 AND 10", name="ck_user_settings_autosave"),
        sa.CheckConstraint("trash_retention_days IN (7, 30, 90) OR trash_retention_days IS NULL", name="ck_user_settings_retention"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_settings")
    op.drop_table("users")
