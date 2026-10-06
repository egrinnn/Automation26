from decimal import Decimal
import pytest
from app import create_app
from app.extensions import db as _db
from app.models import Category, Dish, ROLE_ADMIN, ROLE_STAFF, Role, User


@pytest.fixture()
def app():
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def roles(db):
    admin_role = Role(name=ROLE_ADMIN, description='Администратор')
    staff_role = Role(name=ROLE_STAFF, description='Сотрудник столовой')
    db.session.add_all([admin_role, staff_role])
    db.session.commit()
    return {'admin': admin_role, 'staff': staff_role}


@pytest.fixture()
def admin_user(db, roles):
    user = User(username='admin', full_name='Админ Админов', role=roles['admin'], is_active_account=True)
    user.set_password('adminpass123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def staff_user(db, roles):
    user = User(username='staff', full_name='Сотрудников Сотрудник', role=roles['staff'], is_active_account=True)
    user.set_password('staffpass123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def inactive_user(db, roles):
    user = User(username='disabled', full_name='Уволенный Сотрудник', role=roles['staff'], is_active_account=False)
    user.set_password('whatever123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def category(db):
    cat = Category(name='Супы')
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture()
def dish(db, category):
    item = Dish(
        name='Борщ',
        category=category,
        description='Наваристый борщ со сметаной',
        portion_size=Decimal('300.00'),
        portion_unit='g',
        price=Decimal('180.50'),
        is_available=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def login(client, username, password):
    return client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )
