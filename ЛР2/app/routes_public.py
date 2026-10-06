from collections import OrderedDict
from datetime import date, datetime, timedelta
from flask import Blueprint, abort, redirect, render_template, request, url_for
from app.models import MENU_STATUS_PUBLISHED, Menu

public_bp = Blueprint('public', __name__)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@public_bp.route('/')
def index():
    return redirect(url_for('public.view_menu'))


@public_bp.route('/menu')
def view_menu():
    requested_date = _parse_date(request.args.get('date')) or date.today()

    menu = Menu.query.filter_by(menu_date=requested_date, status=MENU_STATUS_PUBLISHED).first()

    categories = OrderedDict()
    if menu is not None:
        for item in menu.items:  
            category = item.dish.category
            categories.setdefault(category, []).append(item)

    return render_template(
        'public/menu.html',
        menu=menu,
        categories=categories,
        selected_date=requested_date,
        prev_date=requested_date - timedelta(days=1),
        next_date=requested_date + timedelta(days=1),
        today=date.today(),
    )
