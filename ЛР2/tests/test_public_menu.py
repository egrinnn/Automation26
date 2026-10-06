from datetime import date, timedelta

from app.extensions import db
from app.models import Menu, MenuItem, MENU_STATUS_DRAFT, MENU_STATUS_PUBLISHED


def _make_menu(menu_date, status, dish):
    menu = Menu(menu_date=menu_date, status=status)
    db.session.add(menu)
    db.session.flush()
    db.session.add(MenuItem(menu_id=menu.id, dish_id=dish.id, display_order=1))
    db.session.commit()
    return menu


def test_no_menu_shows_empty_state(client):
    response = client.get('/menu?date=2026-12-31')
    assert response.status_code == 200
    assert 'пока не опубликовано'.encode() in response.data


def test_draft_menu_not_visible_to_visitor(client, dish, db):
    _make_menu(date(2026, 10, 5), MENU_STATUS_DRAFT, dish)
    response = client.get('/menu?date=2026-10-05')
    assert 'Борщ'.encode() not in response.data
    assert 'пока не опубликовано'.encode() in response.data


def test_published_menu_visible_with_price(client, dish, db):
    _make_menu(date(2026, 10, 5), MENU_STATUS_PUBLISHED, dish)
    response = client.get('/menu?date=2026-10-05')
    assert response.status_code == 200
    assert 'Борщ'.encode() in response.data
    assert '180,50'.encode() in response.data
    assert 'Супы'.encode() in response.data


def test_unavailable_dish_marked_not_available_not_hidden(client, dish, db):
    dish.is_available = False
    db.session.commit()
    _make_menu(date(2026, 10, 5), MENU_STATUS_PUBLISHED, dish)

    response = client.get('/menu?date=2026-10-05')
    assert 'Борщ'.encode() in response.data
    assert 'нет в наличии'.encode() in response.data


def test_historical_menu_still_viewable(client, dish, db):
    past_date = date.today() - timedelta(days=30)
    _make_menu(past_date, MENU_STATUS_PUBLISHED, dish)

    response = client.get(f'/menu?date={past_date.isoformat()}')
    assert response.status_code == 200
    assert 'Борщ'.encode() in response.data


def test_default_date_is_today(client, dish, db):
    _make_menu(date.today(), MENU_STATUS_PUBLISHED, dish)
    response = client.get('/menu')
    assert response.status_code == 200
    assert 'Борщ'.encode() in response.data
    assert 'сегодня'.encode() in response.data
