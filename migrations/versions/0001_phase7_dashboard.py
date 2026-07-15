"""Phase 7 dashboard schema.

Revision ID: 0001_phase7
"""
from alembic import op
from indusguard.dashboard.database import Base
from indusguard.dashboard import models  # noqa: F401

revision = "0001_phase7"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
