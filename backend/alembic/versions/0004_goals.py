"""goals, tasks, events and review links

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(20), server_default="not_started", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *common(),
        sa.CheckConstraint("status IN ('not_started', 'active', 'completed', 'paused', 'abandoned')", name="ck_goals_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_status", "goals", ["user_id", "status"])
    op.create_table(
        "goal_tasks",
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="todo", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *common(),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'completed')", name="ck_goal_tasks_status"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_tasks_goal_status", "goal_tasks", ["goal_id", "status"])
    op.create_table(
        "goal_events",
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("event_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_events_goal_created", "goal_events", ["goal_id", "created_at"])
    op.create_table(
        "review_goals",
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_id", "goal_id", name="uq_review_goals_pair"),
    )
    op.create_index("ix_review_goals_review_id", "review_goals", ["review_id"])
    op.create_index("ix_review_goals_goal_id", "review_goals", ["goal_id"])


def downgrade() -> None:
    op.drop_table("review_goals")
    op.drop_table("goal_events")
    op.drop_table("goal_tasks")
    op.drop_table("goals")
