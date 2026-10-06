from tests.conftest import login


def _dish_payload(category, **overrides):
    payload = {
        'name': 'Плов',
        'category_id': str(category.id),
        'description': 'С бараниной',
        'portion_size': '250',
        'portion_unit': 'g',
        'price': '220.00',
        'is_available': 'y',
    }
    payload.update(overrides)
    return payload


def test_staff_can_create_dish(client, staff_user, category):
    login(client, 'staff', 'staffpass123')
    response = client.post('/admin/dishes/new', data=_dish_payload(category), follow_redirects=True)
    assert response.status_code == 200
    assert 'Плов'.encode() in response.data


def test_negative_price_rejected(client, staff_user, category):
    login(client, 'staff', 'staffpass123')
    response = client.post(
        '/admin/dishes/new', data=_dish_payload(category, price='-10'), follow_redirects=True
    )
    assert response.status_code == 200
    assert 'должна быть больше нуля'.encode() in response.data


def test_zero_portion_size_rejected(client, staff_user, category):
    login(client, 'staff', 'staffpass123')
    response = client.post(
        '/admin/dishes/new', data=_dish_payload(category, portion_size='0'), follow_redirects=True
    )
    assert response.status_code == 200
    assert 'должна быть больше нуля'.encode() in response.data


def test_missing_name_rejected_and_form_preserves_other_fields(client, staff_user, category):
    """П. 4.2.9: при ошибке исходные корректные данные не должны быть потеряны —
    остальные поля должны остаться заполненными в форме после неудачной отправки."""
    login(client, 'staff', 'staffpass123')
    response = client.post(
        '/admin/dishes/new', data=_dish_payload(category, name=''), follow_redirects=True
    )
    assert response.status_code == 200
    assert 'Укажите название блюда'.encode() in response.data
    assert b'value="220.00"' in response.data


def test_search_by_name(client, staff_user, dish):
    login(client, 'staff', 'staffpass123')
    found = client.get('/admin/dishes/?q=орщ')
    not_found = client.get('/admin/dishes/?q=пицца')
    assert 'Борщ'.encode() in found.data
    assert 'Борщ'.encode() not in not_found.data


def test_filter_by_availability(client, staff_user, dish):
    login(client, 'staff', 'staffpass123')
    client.post(f'/admin/dishes/{dish.id}/archive', follow_redirects=True)

    available_only = client.get('/admin/dishes/?availability=available')
    unavailable_only = client.get('/admin/dishes/?availability=unavailable')
    assert 'Борщ'.encode() not in available_only.data
    assert 'Борщ'.encode() in unavailable_only.data


def test_archive_dish_does_not_delete_it(client, staff_user, dish, db):
    login(client, 'staff', 'staffpass123')
    client.post(f'/admin/dishes/{dish.id}/archive', follow_redirects=True)

    from app.models import Dish

    still_exists = db.session.get(Dish, dish.id)
    assert still_exists is not None
    assert still_exists.is_available is False
