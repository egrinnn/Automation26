from app.models import Menu, MENU_STATUS_DRAFT, MENU_STATUS_PUBLISHED
from tests.conftest import login


def test_staff_can_create_menu(client, staff_user):
    login(client, 'staff', 'staffpass123')
    response = client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    assert response.status_code == 200
    assert '01.10.2026'.encode() in response.data


def test_duplicate_menu_date_rejected(client, staff_user, db):
    login(client, 'staff', 'staffpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    response = client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'уже существует'.encode() in response.data


def test_add_dish_to_menu(client, staff_user, dish, db):
    login(client, 'staff', 'staffpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()

    response = client.post(
        f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True
    )
    assert response.status_code == 200
    assert 'Борщ'.encode() in response.data


def test_cannot_add_same_dish_twice(client, staff_user, dish, db):
    login(client, 'staff', 'staffpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)
    from app.models import MenuItem

    count_before = MenuItem.query.filter_by(menu_id=menu.id, dish_id=dish.id).count()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)
    count_after = MenuItem.query.filter_by(menu_id=menu.id, dish_id=dish.id).count()
    assert count_before == 1
    assert count_after == 1


def test_publish_requires_admin_role(client, staff_user, dish, db):
    login(client, 'staff', 'staffpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)

    response = client.post(f'/admin/menus/{menu.id}/publish')
    assert response.status_code == 403


def test_publish_fails_without_available_item(client, admin_user, db):
    login(client, 'admin', 'adminpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()

    response = client.post(f'/admin/menus/{menu.id}/publish', follow_redirects=True)
    assert response.status_code == 200
    assert 'Нельзя опубликовать'.encode() in response.data
    assert db.session.get(Menu, menu.id).status == MENU_STATUS_DRAFT


def test_publish_succeeds_with_available_item(client, admin_user, dish, db):
    login(client, 'admin', 'adminpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)

    response = client.post(f'/admin/menus/{menu.id}/publish', follow_redirects=True)
    assert response.status_code == 200
    assert db.session.get(Menu, menu.id).status == MENU_STATUS_PUBLISHED


def test_unpublish_returns_menu_to_draft(client, admin_user, dish, db):
    login(client, 'admin', 'adminpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)
    client.post(f'/admin/menus/{menu.id}/publish', follow_redirects=True)

    client.post(f'/admin/menus/{menu.id}/unpublish', follow_redirects=True)
    assert db.session.get(Menu, menu.id).status == MENU_STATUS_DRAFT


def test_remove_item_does_not_delete_dish_from_catalog(client, staff_user, dish, db):
    login(client, 'staff', 'staffpass123')
    client.post('/admin/menus/new', data={'menu_date': '2026-10-01'}, follow_redirects=True)
    menu = Menu.query.filter_by(menu_date='2026-10-01').first()
    client.post(f'/admin/menus/{menu.id}/items', data={'dish_id': str(dish.id)}, follow_redirects=True)

    from app.models import Dish, MenuItem

    item = MenuItem.query.filter_by(menu_id=menu.id, dish_id=dish.id).first()
    client.post(f'/admin/menus/{menu.id}/items/{item.id}/delete', follow_redirects=True)

    assert MenuItem.query.filter_by(menu_id=menu.id, dish_id=dish.id).first() is None
    assert db.session.get(Dish, dish.id) is not None
