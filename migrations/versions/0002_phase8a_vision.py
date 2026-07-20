"""Phase 8A visual detection persistence.

Revision ID: 0002_phase8a_vision
Revises: 0001_phase7
"""
from alembic import op

from indusguard.dashboard.models import VisionDetectionModel

revision = "0002_phase8a_vision"
down_revision = "0001_phase7"
branch_labels = None
depends_on = None


def upgrade():
    VisionDetectionModel.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade():
    VisionDetectionModel.__table__.drop(bind=op.get_bind(), checkfirst=True)
