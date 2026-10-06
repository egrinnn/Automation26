from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

ROLE_ADMIN = 'admin'
ROLE_STAFF = 'staff'
ROLE_CHOICES = (ROLE_ADMIN, ROLE_STAFF)

PORTION_UNIT_GRAM = 'g'
PORTION_UNIT_ML = 'ml'
PORTION_UNIT_CHOICES = (PORTION_UNIT_GRAM, PORTION_UNIT_ML)

MENU_STATUS_DRAFT = 'draft'
MENU_STATUS_PUBLISHED = 'published'
MENU_STATUS_CHOICES = (MENU_STATUS_DRAFT, MENU_STATUS_PUBLISHED)

AUDIT_ACTION_CREATE = 'create'
AUDIT_ACTION_UPDATE = 'update'
AUDIT_ACTION_ARCHIVE = 'archive'
AUDIT_ACTION_RESTORE = 'restore'
AUDIT_ACTION_PUBLISH = 'publish'
AUDIT_ACTION_UNPUBLISH = 'unpublish'


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.String(200))

    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    role = db.relationship('Role', back_populates='users')
    audit_entries = db.relationship('AuditLog', back_populates='user')

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def has_role(self, *role_names: str) -> bool:
        return self.role is not None and self.role.name in role_names

    @property
    def is_active(self):
        return self.is_active_account

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    dishes = db.relationship('Dish', back_populates='category')

    __table_args__ = (
        Index(
            'ix_categories_name_active_unique',
            name,
            unique=True,
            postgresql_where=is_active.is_(True),
        ),
    )

    def __repr__(self):
        return f'<Category {self.name}>'


class Dish(db.Model):

    __tablename__ = 'dishes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text)
    portion_size = db.Column(db.Numeric(8, 2), nullable=False)
    portion_unit = db.Column(db.String(2), nullable=False, default=PORTION_UNIT_GRAM)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    category = db.relationship('Category', back_populates='dishes')
    menu_items = db.relationship('MenuItem', back_populates='dish')

    __table_args__ = (
        CheckConstraint('price > 0', name='price_positive'),
        CheckConstraint('portion_size > 0', name='portion_size_positive'),
        CheckConstraint("portion_unit IN ('g', 'ml')", name='portion_unit_valid'),
    )

    def __repr__(self):
        return f'<Dish {self.name}>'


class Menu(db.Model):

    __tablename__ = 'menus'

    id = db.Column(db.Integer, primary_key=True)
    menu_date = db.Column(db.Date, nullable=False, unique=True)
    status = db.Column(db.String(10), nullable=False, default=MENU_STATUS_DRAFT)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    published_at = db.Column(db.DateTime)

    items = db.relationship(
        'MenuItem',
        back_populates='menu',
        order_by='MenuItem.display_order',
        cascade='all, delete-orphan',
    )

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published')", name='status_valid'),
    )

    @property
    def is_published(self) -> bool:
        return self.status == MENU_STATUS_PUBLISHED

    def __repr__(self):
        return f'<Menu {self.menu_date} {self.status}>'


class MenuItem(db.Model):

    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    menu = db.relationship('Menu', back_populates='items')
    dish = db.relationship('Dish', back_populates='menu_items')

    __table_args__ = (
        UniqueConstraint('menu_id', 'dish_id', name='uq_menu_items_menu_dish'),
    )


class AuditLog(db.Model):

    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(20), nullable=False)
    entity_type = db.Column(db.String(30), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user = db.relationship('User', back_populates='audit_entries')

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}:{self.entity_id}>'
