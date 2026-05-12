"""init workflow tables

Revision ID: 20260506_0001
Revises:
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260506_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_sessions",
        sa.Column("session_id", sa.String(length=64), primary_key=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
    )
    op.create_index("idx_workflow_state", "workflow_sessions", ["state"])
    op.create_index("idx_workflow_updated_at", "workflow_sessions", ["updated_at"])

    op.create_table(
        "analyze_history",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
    )
    op.create_index("idx_history_created_at", "analyze_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_history_created_at", table_name="analyze_history")
    op.drop_table("analyze_history")
    op.drop_index("idx_workflow_updated_at", table_name="workflow_sessions")
    op.drop_index("idx_workflow_state", table_name="workflow_sessions")
    op.drop_table("workflow_sessions")
