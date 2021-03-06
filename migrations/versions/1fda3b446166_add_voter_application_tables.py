"""Add voter application tables

Revision ID: 1fda3b446166
Revises: 3e3cfa9a7b4c
Create Date: 2014-10-19 23:38:10.934509

"""

# revision identifiers, used by Alembic.
revision = '1fda3b446166'
down_revision = '3e3cfa9a7b4c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('consumption_tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=160), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('voter_application',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('primary_team_id', sa.Integer(), nullable=True),
    sa.Column('approach', sa.Text(), nullable=False),
    sa.Column('other_comments', sa.Text(), nullable=True),
    sa.Column('will_participate', sa.Boolean(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['primary_team_id'], ['team.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('application_tags',
    sa.Column('application_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['voter_application.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['consumption_tags.id'], )
    )
    op.create_table('other_teams',
    sa.Column('application_id', sa.Integer(), nullable=True),
    sa.Column('team_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['voter_application.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], )
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('other_teams')
    op.drop_table('application_tags')
    op.drop_table('voter_application')
    op.drop_table('consumption_tags')
    ### end Alembic commands ###
