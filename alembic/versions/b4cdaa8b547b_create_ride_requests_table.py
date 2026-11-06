"""create ride_requests table

Revision ID: b4cdaa8b547b
Revises: 15c32aa5e9a6
Create Date: 2026-05-01 16:54:11.956916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'b4cdaa8b547b'
down_revision: Union[str, Sequence[str], None] = '15c32aa5e9a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ride requests after the initial users and rides tables."""
    op.create_table(
        'ride_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ride_id', sa.UUID(), nullable=False),
        sa.Column('passenger_id', sa.UUID(), nullable=False),
        sa.Column('passenger_origin', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('passenger_destination', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELED', name='requeststatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ride_id'], ['rides.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['passenger_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ride_requests_id'), 'ride_requests', ['id'])


def downgrade() -> None:
    """Remove ride requests and its enum type."""
    op.drop_index(op.f('ix_ride_requests_id'), table_name='ride_requests')
    op.drop_table('ride_requests')
    sa.Enum(name='requeststatus').drop(op.get_bind(), checkfirst=True)
