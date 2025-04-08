from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'create_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Example table creation
    op.create_table(
        'example_table',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('example_table')
