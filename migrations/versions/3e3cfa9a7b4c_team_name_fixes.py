"""Team name fixes

Revision ID: 3e3cfa9a7b4c
Revises: 6a896d0e829
Create Date: 2014-10-17 01:15:22.557639

"""

# revision identifiers, used by Alembic.
revision = '3e3cfa9a7b4c'
down_revision = '6a896d0e829'

from alembic import op
import sqlalchemy as sa


def upgrade():
    team = sa.sql.table('team',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=75), nullable=True),
    sa.Column('short_name', sa.String(length=50), nullable=True),
    sa.Column('flair', sa.String(length=50), nullable=True),
    sa.Column('nickname', sa.String(length=50), nullable=True),
    sa.Column('conference', sa.String(length=50), nullable=True))
    op.execute(
        team.update().\
       	where(team.c.id==107).\
        values({'full_name':op.inline_literal('University of Wisconsin-Green Bay'),
                'short_name':op.inline_literal('Green Bay')})
        )
    op.execute(
        team.update().\
        where(team.c.id==168).\
        values({'full_name':op.inline_literal('University of Wisconsin-Milwaukee')})
        )
    op.execute(
        team.update().\
        where(team.c.id==317).\
        values({'full_name':op.inline_literal('University of Wisconsin-Madison')})
        )
    op.execute(
        team.update().\
        where(team.c.id==111).\
        values({'full_name':op.inline_literal('University of Hawaii at Manoa')})
        )


def downgrade():
    pass
