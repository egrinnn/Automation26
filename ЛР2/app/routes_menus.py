from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.decorators import admin_required, staff_or_admin_required
from app.extensions import db
from app.forms import MenuDateForm, MenuItemForm
from app.models import (
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_PUBLISH,
    AUDIT_ACTION_UNPUBLISH,
    Menu,
    MenuItem,
    utcnow,
)
from app.utils import log_action

menus_bp = Blueprint('menus', __name__, url_prefix='/admin/menus')


@menus_bp.route('/')
@staff_or_admin_required
def list_menus():
    menus = Menu.query.order_by(Menu.menu_date.desc()).all()
    return render_template('menus/list.html', menus=menus)


@menus_bp.route('/new', methods=['GET', 'POST'])
@staff_or_admin_required
def new_menu():
    form = MenuDateForm()
    if form.validate_on_submit():
        menu = Menu(menu_date=form.menu_date.data)
        db.session.add(menu)
        db.session.flush()
        log_action(AUDIT_ACTION_CREATE, 'menu', menu.id, details=str(menu.menu_date))
        db.session.commit()
        flash(f'Меню на {menu.menu_date.strftime("%d.%m.%Y")} создано (черновик).', 'success')
        return redirect(url_for('menus.menu_detail', menu_id=menu.id))
    return render_template('menus/new.html', form=form)


@menus_bp.route('/<int:menu_id>')
@staff_or_admin_required
def menu_detail(menu_id):
    menu = db.get_or_404(Menu, menu_id)
    add_item_form = MenuItemForm()
    add_item_form.set_dish_choices(menu.id)
    can_publish = any(item.dish.is_available for item in menu.items)
    return render_template(
        'menus/detail.html',
        menu=menu,
        add_item_form=add_item_form,
        can_publish=can_publish,
    )


@menus_bp.route('/<int:menu_id>/items', methods=['POST'])
@staff_or_admin_required
def add_menu_item(menu_id):
    menu = db.get_or_404(Menu, menu_id)
    form = MenuItemForm()
    form.set_dish_choices(menu.id)

    if not form.dish_id.choices:
        flash('Все блюда уже добавлены в это меню.', 'warning')
        return redirect(url_for('menus.menu_detail', menu_id=menu.id))

    if form.validate_on_submit():
        next_order = max([item.display_order for item in menu.items], default=0) + 1
        item = MenuItem(menu_id=menu.id, dish_id=form.dish_id.data, display_order=next_order)
        db.session.add(item)
        db.session.commit()
        flash('Блюдо добавлено в меню.', 'success')
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'danger')

    return redirect(url_for('menus.menu_detail', menu_id=menu.id))


@menus_bp.route('/<int:menu_id>/items/<int:item_id>/delete', methods=['POST'])
@staff_or_admin_required
def delete_menu_item(menu_id, item_id):
    item = db.get_or_404(MenuItem, item_id)
    if item.menu_id != menu_id:
        abort(404)
    db.session.delete(item)
    db.session.commit()
    flash('Блюдо убрано из меню.', 'info')
    return redirect(url_for('menus.menu_detail', menu_id=menu_id))


def _swap_order(menu_id, item_id, direction):
    menu = db.get_or_404(Menu, menu_id)
    items = menu.items
    index = next((i for i, it in enumerate(items) if it.id == item_id), None)
    if index is None:
        abort(404)

    target_index = index - 1 if direction == 'up' else index + 1
    if 0 <= target_index < len(items):
        items[index].display_order, items[target_index].display_order = (
            items[target_index].display_order,
            items[index].display_order,
        )
        db.session.commit()


@menus_bp.route('/<int:menu_id>/items/<int:item_id>/move-up', methods=['POST'])
@staff_or_admin_required
def move_item_up(menu_id, item_id):
    _swap_order(menu_id, item_id, 'up')
    return redirect(url_for('menus.menu_detail', menu_id=menu_id))


@menus_bp.route('/<int:menu_id>/items/<int:item_id>/move-down', methods=['POST'])
@staff_or_admin_required
def move_item_down(menu_id, item_id):
    _swap_order(menu_id, item_id, 'down')
    return redirect(url_for('menus.menu_detail', menu_id=menu_id))


@menus_bp.route('/<int:menu_id>/publish', methods=['POST'])
@admin_required
def publish_menu(menu_id):
    menu = db.get_or_404(Menu, menu_id)

    has_active_item = any(item.dish.is_available for item in menu.items)
    if not has_active_item:
        flash('Нельзя опубликовать пустое меню или меню без доступных блюд.', 'danger')
        return redirect(url_for('menus.menu_detail', menu_id=menu.id))

    menu.status = 'published'
    menu.published_at = utcnow()
    log_action(AUDIT_ACTION_PUBLISH, 'menu', menu.id, details=str(menu.menu_date))
    db.session.commit()
    flash(f'Меню на {menu.menu_date.strftime("%d.%m.%Y")} опубликовано.', 'success')
    return redirect(url_for('menus.menu_detail', menu_id=menu.id))


@menus_bp.route('/<int:menu_id>/unpublish', methods=['POST'])
@admin_required
def unpublish_menu(menu_id):
    menu = db.get_or_404(Menu, menu_id)
    menu.status = 'draft'
    log_action(AUDIT_ACTION_UNPUBLISH, 'menu', menu.id, details=str(menu.menu_date))
    db.session.commit()
    flash('Меню снято с публикации и возвращено в черновики.', 'info')
    return redirect(url_for('menus.menu_detail', menu_id=menu.id))
