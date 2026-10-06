from app.models import AuditLog
from tests.conftest import login


def test_staff_cannot_view_audit_log(client, staff_user):
    login(client, 'staff', 'staffpass123')
    response = client.get('/admin/audit/')
    assert response.status_code == 403


def test_category_creation_is_logged(client, admin_user, db):
    login(client, 'admin', 'adminpass123')
    client.post('/admin/categories/new', data={'name': 'Салаты'}, follow_redirects=True)

    entry = AuditLog.query.filter_by(entity_type='category', action='create').first()
    assert entry is not None
    assert entry.details == 'Салаты'
    assert entry.user.username == 'admin'


def test_dish_archive_is_logged(client, staff_user, dish, db):
    login(client, 'staff', 'staffpass123')
    client.post(f'/admin/dishes/{dish.id}/archive', follow_redirects=True)

    entry = AuditLog.query.filter_by(entity_type='dish', action='archive', entity_id=dish.id).first()
    assert entry is not None
    assert entry.user.username == 'staff'


def test_menu_publish_is_logged(client, admin_user, dish, db):
    login(client, 'admin', 'adminpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)

    from app.models import Menu

    menu = Menu.query.filter_by(menu_date='2026-10-01').first()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)
    client.post(f'/admin/menus/{menu.id}/publish', follow_redirects=True)

    entry = AuditLog.query.filter_by(entity_type='menu', action='publish', entity_id=menu.id).first()
    assert entry is not None
