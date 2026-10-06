import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import ROLE_ADMIN, ROLE_STAFF, Role, User


def register_cli_commands(app):
    app.cli.add_command(seed_roles_command)
    app.cli.add_command(create_admin_command)


@click.command('seed-roles')
@with_appcontext
def seed_roles_command():
    created = []
    defaults = {
        ROLE_ADMIN: 'Администратор',
        ROLE_STAFF: 'Сотрудник столовой',
    }
    for name, description in defaults.items():
        if Role.query.filter_by(name=name).first() is None:
            db.session.add(Role(name=name, description=description))
            created.append(name)
    db.session.commit()
    if created:
        click.echo(f'Созданы роли: {", ".join(created)}')
    else:
        click.echo('Роли уже существуют, пропускаю.')


@click.command('create-admin')
@click.option('--username', prompt='Логин администратора', help='Логин для входа.')
@click.option(
    '--password',
    prompt='Пароль администратора',
    hide_input=True,
    confirmation_prompt=True,
    help='Пароль (не хранится в открытом виде).',
)
@click.option('--full-name', prompt='Полное имя', default='Администратор', help='Отображаемое имя.')
@with_appcontext
def create_admin_command(username, password, full_name):
    """Создаёт учётную запись администратора для первого входа в систему."""
    role = Role.query.filter_by(name=ROLE_ADMIN).first()
    if role is None:
        click.echo('Роль "admin" не найдена. Сначала выполните: flask seed-roles')
        raise SystemExit(1)

    if User.query.filter(db.func.lower(User.username) == username.strip().lower()).first():
        click.echo(f'Пользователь "{username}" уже существует.')
        raise SystemExit(1)

    user = User(username=username.strip(), full_name=full_name.strip(), role=role, is_active_account=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Администратор "{username}" создан.')
