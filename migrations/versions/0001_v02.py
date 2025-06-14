from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('document', sa.Column('friendly_name', sa.String(length=120), index=True, nullable=True))
    op.add_column('document', sa.Column('instructions', sa.Text(), nullable=True))
    op.add_column('document', sa.Column('desired_q', sa.Integer(), nullable=True, server_default='10'))
    op.add_column('document', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('quiz', sa.Column('friendly_name', sa.String(length=120), index=True, nullable=True))

def downgrade():
    op.drop_column('quiz', 'friendly_name')
    op.drop_column('document', 'content')
    op.drop_column('document', 'desired_q')
    op.drop_column('document', 'instructions')
    op.drop_column('document', 'friendly_name')
