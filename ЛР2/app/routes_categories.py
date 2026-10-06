from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from app.decorators import admin_required
from app.extensions import db
from app.forms import CategoryForm
from app.models import AUDIT_ACTION_ARCHIVE, AUDIT_ACTION_CREATE, AUDIT_ACTION_RESTORE, AUDIT_ACTION_UPDATE, Category
from app.utils import log_action

categories_bp = Blueprint('categories', __name__, url_prefix='/admin/categories')


@categories_bp.route('/')
@admin_required
def list_categories():
    show_archived = request.args.get('show') == 'all'
    query = Category.query
    if not show_archived:
        query = query.filter_by(is_active=True)
    categories = query.order_by(Category.name).all()
    return render_template('categories/list.html', categories=categories, show_archived=show_archived)


@categories_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data.strip())
        db.session.add(category)
        db.session.flush() 
        log_action(AUDIT_ACTION_CREATE, 'category', category.id, details=category.name)
        db.session.commit()
        flash(f'Категория «{category.name}» создана.', 'success')
        return redirect(url_for('categories.list_categories'))
    return render_template('categories/form.html', form=form, category=None)


@categories_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = db.get_or_404(Category, category_id)
    form = CategoryForm(obj=category, category_id=category.id)
    if form.validate_on_submit():
        category.name = form.name.data.strip()
        log_action(AUDIT_ACTION_UPDATE, 'category', category.id, details=category.name)
        db.session.commit()
        flash(f'Категория «{category.name}» обновлена.', 'success')
        return redirect(url_for('categories.list_categories'))
    return render_template('categories/form.html', form=form, category=category)


@categories_bp.route('/<int:category_id>/archive', methods=['POST'])
@admin_required
def archive_category(category_id):
    category = db.get_or_404(Category, category_id)
    category.is_active = False
    log_action(AUDIT_ACTION_ARCHIVE, 'category', category.id, details=category.name)
    db.session.commit()
    flash(f'Категория «{category.name}» перенесена в архив.', 'info')
    return redirect(url_for('categories.list_categories'))


@categories_bp.route('/<int:category_id>/restore', methods=['POST'])
@admin_required
def restore_category(category_id):
    category = db.get_or_404(Category, category_id)
    duplicate = Category.query.filter(
        db.func.lower(Category.name) == category.name.strip().lower(),
        Category.is_active.is_(True),
        Category.id != category.id,
    ).first()
    if duplicate is not None:
        flash(
            f'Нельзя восстановить: активная категория «{duplicate.name}» уже существует. '
            'Сначала переименуйте одну из них.',
            'danger',
        )
        return redirect(url_for('categories.list_categories', show='all'))

    category.is_active = True
    log_action(AUDIT_ACTION_RESTORE, 'category', category.id, details=category.name)
    db.session.commit()
    flash(f'Категория «{category.name}» восстановлена.', 'success')
    return redirect(url_for('categories.list_categories'))
