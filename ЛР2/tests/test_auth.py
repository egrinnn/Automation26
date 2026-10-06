from tests.conftest import login


def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert 'Вход для сотрудников'.encode() in response.data


def test_login_success_redirects_by_role(client, admin_user):
    response = login(client, 'admin', 'adminpass123')
    assert response.status_code == 200
    assert 'Вход для сотрудников'.encode() not in response.data


def test_login_wrong_password_shows_generic_error(client, admin_user):
    response = login(client, 'admin', 'wrong-password')
    assert response.status_code == 200
    assert 'Неверный логин или пароль'.encode() in response.data


def test_login_unknown_username_shows_same_generic_error(client, admin_user):
    response_unknown = login(client, 'ghost', 'whatever123')
    response_wrong_pw = login(client, 'admin', 'wrong-password')
    assert 'Неверный логин или пароль'.encode() in response_unknown.data
    assert 'Неверный логин или пароль'.encode() in response_wrong_pw.data


def test_login_inactive_account_rejected(client, inactive_user):
    response = login(client, 'disabled', 'whatever123')
    assert response.status_code == 200
    assert 'Неверный логин или пароль'.encode() in response.data


def test_anonymous_redirected_to_login_from_admin_page(client):
    response = client.get('/admin/dishes/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_logout_ends_session(client, admin_user):
    login(client, 'admin', 'adminpass123')
    client.get('/logout')
    response = client.get('/admin/dishes/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
