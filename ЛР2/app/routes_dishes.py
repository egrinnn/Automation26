from flask import Blueprint, flash, redirect, render_template, request, url_for
from app.decorators import staff_or_admin_required
from app.extensions import db
from app.forms import DishForm
from app.models import AUDIT_ACTION_ARCHIVE, AUDIT_ACTION_CREATE, AUDIT_ACTION_RESTORE, AUDIT_ACTION_UPDATE, Category, Dish
from app.utils import log_action

dishes_bp = Blueprint('dishes', __name__, url_prefix='/admin/dishes')


@dishes_bp.route('/')
@staff_or_admin_required
def list_dishes():
    search = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    availability = request.args.get('availability')  

    query = Dish.query
    if search:
        query = query.filter(Dish.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter(Dish.category_id == category_id)
    if availability == 'available':
        query = query.filter(Dish.is_available.is_(True))
    elif availability == 'unavailable':
        query = query.filter(Dish.is_available.is_(False))

    dishes = query.order_by(Dish.name).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()

    return render_template(
        'dishes/list.html',
        dishes=dishes,
        categories=categories,
        search=search,
        selected_category_id=category_id,
        availability=availability,
    )


@dishes_bp.route('/new', methods=['GET', 'POST'])
@staff_or_admin_required
def new_dish():
    form = DishForm()
    form.set_category_choices()

    if not form.category_id.choices:
        flash('Сначала создайте хотя бы одну категорию — без категории блюдо не сохранить.', 'warning')
        return redirect(url_for('categories.list_categories'))

    if form.validate_on_submit():
        dish = Dish(
            name=form.name.data.strip(),
            category_id=form.category_id.data,
            description=(form.description.data or '').strip() or None,
            portion_size=form.portion_size.data,
            portion_unit=form.portion_unit.data,
            price=form.price.data,
            is_available=form.is_available.data,
        )
        db.session.add(dish)
        db.session.flush()
        log_action(AUDIT_ACTION_CREATE, 'dish', dish.id, details=dish.name)
        db.session.commit()
        flash(f'Блюдо «{dish.name}» добавлено.', 'success')
        return redirect(url_for('dishes.list_dishes'))

    return render_template('dishes/form.html', form=form, dish=None)


@dishes_bp.route('/<int:dish_id>/edit', methods=['GET', 'POST'])
@staff_or_admin_required
def edit_dish(dish_id):
    dish = db.get_or_404(Dish, dish_id)
    form = DishForm(obj=dish)
    form.set_category_choices(include_category_id=dish.category_id)

    if form.validate_on_submit():
        dish.name = form.name.data.strip()
        dish.category_id = form.category_id.data
        dish.description = (form.description.data or '').strip() or None
        dish.portion_size = form.portion_size.data
        dish.portion_unit = form.portion_unit.data
        dish.price = form.price.data
        dish.is_available = form.is_available.data
        log_action(AUDIT_ACTION_UPDATE, 'dish', dish.id, details=dish.name)
        db.session.commit()
        flash(f'Блюдо «{dish.name}» обновлено.', 'success')
        return redirect(url_for('dishes.list_dishes'))

    return render_template('dishes/form.html', form=form, dish=dish)


@dishes_bp.route('/<int:dish_id>/archive', methods=['POST'])
@staff_or_admin_required
def archive_dish(dish_id):
    dish = db.get_or_404(Dish, dish_id)
    dish.is_available = False
    log_action(AUDIT_ACTION_ARCHIVE, 'dish', dish.id, details=dish.name)
    db.session.commit()
    flash(f'Блюдо «{dish.name}» помечено как недоступное.', 'info')
    return redirect(url_for('dishes.list_dishes'))


@dishes_bp.route('/<int:dish_id>/restore', methods=['POST'])
@staff_or_admin_required
def restore_dish(dish_id):
    dish = db.get_or_404(Dish, dish_id)
    dish.is_available = True
    log_action(AUDIT_ACTION_RESTORE, 'dish', dish.id, details=dish.name)
    db.session.commit()
    flash(f'Блюдо «{dish.name}» снова доступно.', 'success')
    return redirect(url_for('dishes.list_dishes'))
