from tests.conftest import login


def test_staff_cannot_access_categories(client, staff_user):
    login(client, 'staff', 'staffpass123')
    response = client.get('/admin/categories/')
    assert response.status_code == 403


def test_admin_can_create_category(client, admin_user):
    login(client, 'admin', 'adminpass123')
    response = client.post('/admin/categories/new', data={'name': 'Салаты'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Салаты'.encode() in response.data


def test_duplicate_active_category_name_rejected(client, admin_user, category):
    login(client, 'admin', 'adminpass123')
    response = client.post('/admin/categories/new', data={'name': 'Супы'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'уже существует'.encode() in response.data


def test_archived_category_name_can_be_reused(client, admin_user, category, db):
    login(client, 'admin', 'adminpass123')
    client.post(f'/admin/categories/{category.id}/archive', follow_redirects=True)
    response = client.post('/admin/categories/new', data={'name': 'Супы'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'уже существует'.encode() not in response.data


def test_restore_blocked_when_name_conflicts_with_active(client, admin_user, category, db):
    login(client, 'admin', 'adminpass123')
    client.post(f'/admin/categories/{category.id}/archive', follow_redirects=True)
    client.post('/admin/categories/new', data={'name': 'Супы'}, follow_redirects=True)
    response = client.post(f'/admin/categories/{category.id}/restore', follow_redirects=True)
    assert response.status_code == 200
    assert 'Нельзя восстановить'.encode() in response.data
