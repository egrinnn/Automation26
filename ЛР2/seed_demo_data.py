from datetime import date, timedelta
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Category, Dish, Menu, MenuItem, ROLE_STAFF, Role, User

app = create_app('development')

with app.app_context():
    staff_role = Role.query.filter_by(name=ROLE_STAFF).first()

    staff = User(username='staff', full_name='Кузнецов Пётр Сергеевич', role=staff_role, is_active_account=True)
    staff.set_password('staffpass123')
    db.session.add(staff)

    categories_data = ['Супы', 'Салаты', 'Горячие блюда', 'Гарниры', 'Напитки', 'Десерты']
    categories = {}
    for name in categories_data:
        c = Category(name=name)
        db.session.add(c)
        categories[name] = c
    db.session.flush()

    dishes_data = [
        ('Борщ со сметаной', 'Супы', 'Наваристый борщ на говяжьем бульоне, подаётся со сметаной', 300, 'g', 180.00, True),
        ('Суп-лапша куриная', 'Супы', 'Домашняя лапша, куриное филе, морковь', 300, 'g', 160.00, True),
        ('Крем-суп из брокколи', 'Супы', 'Сливочный суп-пюре из брокколи с гренками', 250, 'g', 190.00, False),
        ('Салат Цезарь с курицей', 'Салаты', 'Романо, куриное филе гриль, пармезан, соус цезарь', 220, 'g', 260.00, True),
        ('Салат Витаминный', 'Салаты', 'Капуста, морковь, яблоко, растительное масло', 180, 'g', 120.00, True),
        ('Котлета по-киевски', 'Горячие блюда', 'Куриная котлета со сливочным маслом и зеленью', 200, 'g', 240.00, True),
        ('Плов с бараниной', 'Горячие блюда', 'Классический плов с бараниной и морковью', 300, 'g', 260.00, True),
        ('Рыба под маринадом', 'Горячие блюда', 'Судак с овощным маринадом', 220, 'g', 250.00, False),
        ('Картофельное пюре', 'Гарниры', 'Пюре на сливочном масле и молоке', 200, 'g', 90.00, True),
        ('Рис отварной', 'Гарниры', 'Рассыпчатый рис с зеленью', 200, 'g', 80.00, True),
        ('Компот из сухофруктов', 'Напитки', 'Компот без сахара', 250, 'ml', 60.00, True),
        ('Чай чёрный', 'Напитки', 'Классический чёрный чай', 200, 'ml', 40.00, True),
        ('Морс клюквенный', 'Напитки', 'Домашний клюквенный морс', 250, 'ml', 70.00, True),
        ('Штрудель яблочный', 'Десерты', 'Слоёный штрудель с яблоками и корицей', 150, 'g', 130.00, True),
        ('Чизкейк Нью-Йорк', 'Десерты', 'Классический чизкейк на песочной основе', 130, 'g', 170.00, True),
    ]

    dishes = {}
    for name, cat_name, desc, size, unit, price, avail in dishes_data:
        d = Dish(
            name=name,
            category=categories[cat_name],
            description=desc,
            portion_size=Decimal(str(size)),
            portion_unit=unit,
            price=Decimal(str(price)),
            is_available=avail,
        )
        db.session.add(d)
        dishes[name] = d
    db.session.flush()

    # Опубликованное меню на сегодня — то, что увидит посетитель.
    today_menu = Menu(menu_date=date.today(), status='published')
    db.session.add(today_menu)
    db.session.flush()

    today_items = [
        'Борщ со сметаной', 'Суп-лапша куриная', 'Крем-суп из брокколи',
        'Салат Цезарь с курицей', 'Салат Витаминный',
        'Котлета по-киевски', 'Плов с бараниной', 'Рыба под маринадом',
        'Картофельное пюре', 'Рис отварной',
        'Компот из сухофруктов', 'Чай чёрный',
        'Штрудель яблочный', 'Чизкейк Нью-Йорк',
    ]
    for i, name in enumerate(today_items, start=1):
        db.session.add(MenuItem(menu_id=today_menu.id, dish_id=dishes[name].id, display_order=i))

    tomorrow_menu = Menu(menu_date=date.today() + timedelta(days=1), status='draft')
    db.session.add(tomorrow_menu)
    db.session.flush()
    for i, name in enumerate(['Суп-лапша куриная', 'Плов с бараниной', 'Морс клюквенный'], start=1):
        db.session.add(MenuItem(menu_id=tomorrow_menu.id, dish_id=dishes[name].id, display_order=i))

    db.session.commit()
    print('Демо-данные созданы: категорий —', len(categories), '| блюд —', len(dishes))
