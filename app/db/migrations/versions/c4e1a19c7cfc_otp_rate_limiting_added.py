"""Otp rate limiting added

Revision ID: c4e1a19c7cfc
Revises: 023cf9db1030
Create Date: 2025-02-16 12:47:23.241995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e1a19c7cfc'
down_revision: Union[str, None] = '023cf9db1030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('password_reset_opts', sa.Column('attempts', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('password_reset_opts', 'attempts')
    # ### end Alembic commands ###
