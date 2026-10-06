from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import LoginForm
from app.models import ROLE_ADMIN, User

auth_bp = Blueprint('auth', __name__)


def _default_landing_url() -> str:
    if current_user.is_authenticated and current_user.has_role(ROLE_ADMIN):
        return url_for('users.list_users')
    return url_for('dishes.list_dishes')


def _is_safe_next_url(target: str) -> bool:
    if not target:
        return False
    parts = urlsplit(target)
    return not parts.netloc and not parts.scheme


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_default_landing_url())

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            User.username.ilike(form.username.data.strip())
        ).first()

        if user is None or not user.check_password(form.password.data) or not user.is_active:
            flash('Неверный логин или пароль.', 'danger')
            return render_template('auth/login.html', form=form)

        login_user(user)
        next_url = request.args.get('next')
        if next_url and _is_safe_next_url(next_url):
            return redirect(next_url)
        return redirect(_default_landing_url())

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))
