import logging
import os
from decimal import Decimal

from flask import Flask, render_template

from app.extensions import csrf, db, login_manager, migrate
from config import config_by_name


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    _register_error_handlers(app)
    _register_template_helpers(app)
    _configure_logging(app)

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.routes_audit import audit_bp
    from app.routes_auth import auth_bp
    from app.routes_categories import categories_bp
    from app.routes_dishes import dishes_bp
    from app.routes_menus import menus_bp
    from app.routes_public import public_bp
    from app.routes_users import users_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(dishes_bp)
    app.register_blueprint(menus_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(audit_bp)


def _register_cli(app: Flask) -> None:
    from app.cli import register_cli_commands

    register_cli_commands(app)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception('Внутренняя ошибка сервера: %s', error)
        return render_template('errors/500.html'), 500


def _register_template_helpers(app: Flask) -> None:
    @app.template_filter('money')
    def money_filter(value) -> str:
        if value is None:
            return '—'
        value = Decimal(value)
        return f'{value:,.2f}'.replace(',', ' ').replace('.', ',')

    @app.template_filter('ru_date')
    def ru_date_filter(value) -> str:
        if value is None:
            return '—'
        months = (
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
        )
        return f'{value.day} {months[value.month - 1]} {value.year}'

    @app.template_filter('ru_plural')
    def ru_plural_filter(n: int, forms: str) -> str:
        one, few, many = [f.strip() for f in forms.split(',')]
        n_abs = abs(int(n))
        if n_abs % 10 == 1 and n_abs % 100 != 11:
            return one
        if 2 <= n_abs % 10 <= 4 and not (12 <= n_abs % 100 <= 14):
            return few
        return many

    @app.context_processor
    def inject_globals():
        from app.models import MENU_STATUS_PUBLISHED

        return {'MENU_STATUS_PUBLISHED': MENU_STATUS_PUBLISHED}


def _configure_logging(app: Flask) -> None:
    if not app.debug and not app.testing:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
