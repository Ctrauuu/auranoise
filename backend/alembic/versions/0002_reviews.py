"""reviews, sections, presets and template

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(12), server_default="draft", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("status IN ('draft', 'completed')", name="ck_reviews_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "review_date", name="uq_reviews_user_date"),
    )
    op.create_index("ix_reviews_user_date", "reviews", ["user_id", "review_date"])
    op.create_index("ix_reviews_user_status", "reviews", ["user_id", "status"])
    op.create_table(
        "review_section_presets",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_section_presets_user_id", "review_section_presets", ["user_id"])
    op.create_index("ix_presets_user_title", "review_section_presets", ["user_id", "title"])
    op.create_table(
        "review_templates",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "review_template_items",
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["template_id"], ["review_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_template_items_order", "review_template_items", ["template_id", "sort_order"])
    op.create_table(
        "review_sections",
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("preset_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("content_markdown", sa.Text(), server_default="", nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["preset_id"], ["review_section_presets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_sections_order", "review_sections", ["review_id", "sort_order"])


def downgrade() -> None:
    op.drop_table("review_sections")
    op.drop_table("review_template_items")
    op.drop_table("review_templates")
    op.drop_table("review_section_presets")
    op.drop_table("reviews")

