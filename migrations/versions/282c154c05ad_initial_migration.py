"""Initial migration

Revision ID: 282c154c05ad
Revises: 
Create Date: 2025-05-18 08:49:35.608839

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '282c154c05ad'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=150), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('google_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('profile_pic', sa.String(length=512), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('google_id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('boars',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('BoarId', sa.String(length=20), nullable=False),
    sa.Column('Breed', sa.String(length=50), nullable=False),
    sa.Column('DOB', sa.Date(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('BoarId', 'user_id', name='uix_boarid_userid')
    )
    with op.batch_alter_table('boars', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_boars_BoarId'), ['BoarId'], unique=False)
        batch_op.create_index(batch_op.f('ix_boars_Breed'), ['Breed'], unique=False)

    op.create_table('expense',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('invoice_number', sa.String(length=100), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('vendor', sa.String(length=100), nullable=True),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'invoice_number', name='uix_user_receipt')
    )
    op.create_table('invoice',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('invoice_number', sa.String(length=50), nullable=False),
    sa.Column('company_name', sa.String(length=255), nullable=False),
    sa.Column('num_of_pigs', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('total_weight', sa.Float(), nullable=False),
    sa.Column('average_weight', sa.Float(), nullable=False),
    sa.Column('total_price', sa.Float(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('invoice_number', 'user_id', name='uix_invoiceid_userid')
    )
    op.create_table('sows',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sowID', sa.String(length=20), nullable=False),
    sa.Column('Breed', sa.String(length=50), server_default='UNKNOWN', nullable=False),
    sa.Column('DOB', sa.Date(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sowID', 'user_id', name='uix_sowid_userid')
    )
    with op.batch_alter_table('sows', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sows_Breed'), ['Breed'], unique=False)
        batch_op.create_index(batch_op.f('ix_sows_sowID'), ['sowID'], unique=False)

    op.create_table('service_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sow_id', sa.Integer(), nullable=False),
    sa.Column('service_date', sa.Date(), nullable=False),
    sa.Column('boar_used', sa.String(length=50), nullable=False),
    sa.Column('checkup_date', sa.Date(), nullable=True),
    sa.Column('litter_guard1_date', sa.Date(), nullable=True),
    sa.Column('litter_guard2_date', sa.Date(), nullable=True),
    sa.Column('feed_up_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('action_date', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['sow_id'], ['sows.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sow_id', 'service_date', name='uix_sow_service_date')
    )
    op.create_table('litter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('service_record_id', sa.Integer(), nullable=False),
    sa.Column('farrowDate', sa.Date(), nullable=False),
    sa.Column('totalBorn', sa.Integer(), nullable=False),
    sa.Column('stillBorn', sa.Integer(), nullable=False),
    sa.Column('bornAlive', sa.Integer(), nullable=False),
    sa.Column('iron_injection_date', sa.Date(), nullable=False),
    sa.Column('tail_dorking_date', sa.Date(), nullable=False),
    sa.Column('teeth_clipping_date', sa.Date(), nullable=False),
    sa.Column('castration_date', sa.Date(), nullable=False),
    sa.Column('wean_date', sa.Date(), nullable=False),
    sa.Column('averageWeight', sa.Float(), nullable=True),
    sa.Column('sow_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['service_record_id'], ['service_records.id'], name='fk_service_record_id', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sow_id'], ['sows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('litter')
    op.drop_table('service_records')
    with op.batch_alter_table('sows', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sows_sowID'))
        batch_op.drop_index(batch_op.f('ix_sows_Breed'))

    op.drop_table('sows')
    op.drop_table('invoice')
    op.drop_table('expense')
    with op.batch_alter_table('boars', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_boars_Breed'))
        batch_op.drop_index(batch_op.f('ix_boars_BoarId'))

    op.drop_table('boars')
    op.drop_table('user')
    # ### end Alembic commands ###
