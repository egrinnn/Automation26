from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user
from app.decorators import admin_required
from app.extensions import db
from app.forms import UserCreateForm, UserEditForm, role_choices
from app.models import ROLE_ADMIN, Role, User

users_bp = Blueprint('users', __name__, url_prefix='/admin/users')


@users_bp.route('/')
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('users/list.html', users=users)


@users_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    form = UserCreateForm()
    form.role_id.choices = role_choices()

    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            full_name=form.full_name.data.strip(),
            role_id=form.role_id.data,
            is_active_account=form.is_active_account.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Пользователь «{user.username}» создан.', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/form.html', form=form, user=None)


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    form = UserEditForm(obj=user)
    form.role_id.choices = role_choices()

    if form.validate_on_submit():
        is_self = user.id == current_user.id
        becomes_non_admin = db.session.get(Role, form.role_id.data).name != ROLE_ADMIN
        becomes_inactive = not form.is_active_account.data

        if is_self and (becomes_non_admin or becomes_inactive):
            flash('Нельзя лишить себя роли администратора или деактивировать свою же учётную запись.', 'danger')
            return render_template('users/form.html', form=form, user=user)

        user.full_name = form.full_name.data.strip()
        user.role_id = form.role_id.data
        user.is_active_account = form.is_active_account.data
        if form.new_password.data:
            user.set_password(form.new_password.data)

        db.session.commit()
        flash(f'Пользователь «{user.username}» обновлён.', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/form.html', form=form, user=user)
