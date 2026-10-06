from tests.conftest import login


def test_staff_cannot_access_users(client, staff_user):
    login(client, 'staff', 'staffpass123')
    response = client.get('/admin/users/')
    assert response.status_code == 403

def test_admin_can_create_user(client, admin_user, roles):
    login(client, 'admin', 'adminpass123')
    response = client.post(
        '/admin/users/new',
        data={
            'username': 'newstaff',
            'full_name': 'Новый Сотрудник',
            'role_id': str(roles['staff'].id),
            'password': 'somepassword1',
            'confirm_password': 'somepassword1',
            'is_active_account': 'y',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'newstaff'.encode() in response.data


def test_admin_cannot_deactivate_own_account(client, admin_user, roles):
    login(client, 'admin', 'adminpass123')
    response = client.post(
        f'/admin/users/{admin_user.id}/edit',
        data={
            'full_name': admin_user.full_name,
            'role_id': str(roles['admin'].id),
            'new_password': '',
            'confirm_password': '',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'Нельзя лишить себя роли'.encode() in response.data

    from app.extensions import db
    from app.models import User

    refreshed = db.session.get(User, admin_user.id)
    assert refreshed.is_active_account is True


def test_admin_cannot_demote_self_from_admin(client, admin_user, roles):
    login(client, 'admin', 'adminpass123')
    response = client.post(
        f'/admin/users/{admin_user.id}/edit',
        data={
            'full_name': admin_user.full_name,
            'role_id': str(roles['staff'].id),
            'is_active_account': 'y',
            'new_password': '',
            'confirm_password': '',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'Нельзя лишить себя роли'.encode() in response.data
