from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column, table


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_categories'))
    )
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.create_index('ix_categories_name_active_unique', ['name'], unique=True, postgresql_where=sa.text('is_active IS true'))

    op.create_table('menus',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('menu_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("status IN ('draft', 'published')", name=op.f('ck_menus_status_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_menus')),
    sa.UniqueConstraint('menu_date', name=op.f('uq_menus_menu_date'))
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
    sa.UniqueConstraint('name', name=op.f('uq_roles_name'))
    )

    roles_table = table(
        'roles',
        column('name', sa.String),
        column('description', sa.String),
    )
    op.bulk_insert(roles_table, [
        {'name': 'admin', 'description': 'Администратор'},
        {'name': 'staff', 'description': 'Сотрудник столовой'},
    ])

    op.create_table('dishes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('portion_size', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('portion_unit', sa.String(length=2), nullable=False),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('is_available', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("portion_unit IN ('g', 'ml')", name=op.f('ck_dishes_portion_unit_valid')),
    sa.CheckConstraint('portion_size > 0', name=op.f('ck_dishes_portion_size_positive')),
    sa.CheckConstraint('price > 0', name=op.f('ck_dishes_price_positive')),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name=op.f('fk_dishes_category_id_categories')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_dishes'))
    )
    with op.batch_alter_table('dishes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_dishes_name'), ['name'], unique=False)

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=120), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('is_active_account', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)

    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=20), nullable=False),
    sa.Column('entity_type', sa.String(length=30), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('details', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_log_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log'))
    )
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_audit_log_created_at'), ['created_at'], unique=False)

    op.create_table('menu_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('menu_id', sa.Integer(), nullable=False),
    sa.Column('dish_id', sa.Integer(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], name=op.f('fk_menu_items_dish_id_dishes')),
    sa.ForeignKeyConstraint(['menu_id'], ['menus.id'], name=op.f('fk_menu_items_menu_id_menus')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_menu_items')),
    sa.UniqueConstraint('menu_id', 'dish_id', name='uq_menu_items_menu_dish')
    )


def downgrade():
    op.drop_table('menu_items')
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_audit_log_created_at'))

    op.drop_table('audit_log')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))

    op.drop_table('users')
    with op.batch_alter_table('dishes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dishes_name'))

    op.drop_table('dishes')
    op.drop_table('roles')
    op.drop_table('menus')
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_index('ix_categories_name_active_unique', postgresql_where=sa.text('is_active IS true'))

    op.drop_table('categories')