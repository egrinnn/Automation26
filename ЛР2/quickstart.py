# -*- coding: utf-8 -*-
"""
Быстрый запуск БЕЗ установки PostgreSQL и без ручных консольных команд.

Что делает этот файл:
1. Использует локальный файл SQLite (quickstart.db в этой же папке)
   вместо PostgreSQL — ничего дополнительно устанавливать не нужно,
   SQLite уже встроен в Python.
2. Сам создаёт все таблицы, роли, тестового администратора и немного
   демонстрационных данных (если их ещё нет).
3. Сам запускает сервер.

Как использовать в VS Code:
    Откройте этот файл и нажмите ▷ ("Run Python File") в правом верхнем
    углу — либо правой кнопкой по файлу → "Run Python File in Terminal".
    Ничего вводить не нужно.

После запуска откройте в браузере:
    http://127.0.0.1:5000/menu   — публичное меню
    http://127.0.0.1:5000/login  — вход: admin / admin12345

ВАЖНО: это временный, упрощённый режим для локального просмотра.
Для реальной сдачи лабораторной нужен PostgreSQL и запуск через
`flask db upgrade` (см. README.md, раздел "Установка и запуск") —
именно так, как требует ТЗ. SQLite здесь используется только потому,
что не поддерживает один нюанс схемы (частичный уникальный индекс на
активных категориях работает как обычный уникальный индекс), это не
влияет на работу форм в браузере, но не тождественно "боевой" схеме.
"""
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quickstart.db')
os.environ['DATABASE_URL'] = 'sqlite:///' + DB_FILE
os.environ.setdefault('SECRET_KEY', 'quickstart-local-only-not-for-production')

from app import create_app                     # noqa: E402
from app.extensions import db                    # noqa: E402
from app.models import (                          # noqa: E402
    Category, Dish, Menu, MenuItem,
    ROLE_ADMIN, ROLE_STAFF, Role, User,
)

app = create_app('development')


def setup_database():
    with app.app_context():
        db.create_all()

        if Role.query.count() == 0:
            db.session.add_all([
                Role(name=ROLE_ADMIN, description='Администратор'),
                Role(name=ROLE_STAFF, description='Сотрудник столовой'),
            ])
            db.session.commit()
            print('Созданы роли: admin, staff')

        if User.query.filter_by(username='admin').first() is None:
            admin_role = Role.query.filter_by(name=ROLE_ADMIN).first()
            user = User(username='admin', full_name='Тестовый администратор',
                        role=admin_role, is_active_account=True)
            user.set_password('admin12345')
            db.session.add(user)
            db.session.commit()
            print('Создан администратор: логин admin / пароль admin12345')

        if Category.query.count() == 0:
            supy = Category(name='Супы')
            goryachee = Category(name='Горячие блюда')
            napitki = Category(name='Напитки')
            db.session.add_all([supy, goryachee, napitki])
            db.session.flush()

            borsch = Dish(name='Борщ со сметаной', category=supy,
                          description='Наваристый борщ на говяжьем бульоне',
                          portion_size=300, portion_unit='g', price=180, is_available=True)
            kotleta = Dish(name='Котлета по-киевски', category=goryachee,
                           description='Куриная котлета со сливочным маслом',
                           portion_size=200, portion_unit='g', price=240, is_available=True)
            chai = Dish(name='Чай чёрный', category=napitki,
                        description='Классический чёрный чай',
                        portion_size=200, portion_unit='ml', price=40, is_available=True)
            db.session.add_all([borsch, kotleta, chai])
            db.session.flush()

            from datetime import date
            menu = Menu(menu_date=date.today(), status='published')
            db.session.add(menu)
            db.session.flush()
            db.session.add_all([
                MenuItem(menu_id=menu.id, dish_id=borsch.id, display_order=1),
                MenuItem(menu_id=menu.id, dish_id=kotleta.id, display_order=2),
                MenuItem(menu_id=menu.id, dish_id=chai.id, display_order=3),
            ])
            db.session.commit()
            print('Добавлены демонстрационные категории, блюда и опубликованное меню на сегодня')


if __name__ == '__main__':
    setup_database()
    print('\n' + '=' * 60)
    print('Готово! Открывайте в браузере:')
    print('  http://127.0.0.1:5000/menu   — публичное меню')
    print('  http://127.0.0.1:5000/login  — вход: admin / admin12345')
    print('=' * 60 + '\n')
    app.run(debug=True, use_reloader=False)
