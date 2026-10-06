from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, InputRequired, Length, NumberRange, Optional, ValidationError

from app.extensions import db
from app.models import Category, Dish, Menu, PORTION_UNIT_CHOICES, ROLE_CHOICES, User


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(message='Введите логин.')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Введите пароль.')])


class CategoryForm(FlaskForm):
    name = StringField(
        'Название категории',
        validators=[DataRequired(message='Укажите название категории.'), Length(max=100)],
    )

    def __init__(self, *args, category_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._category_id = category_id

    def validate_name(self, field):
        query = Category.query.filter(
            db.func.lower(Category.name) == field.data.strip().lower(),
            Category.is_active.is_(True),
        )
        if self._category_id is not None:
            query = query.filter(Category.id != self._category_id)
        if query.first() is not None:
            raise ValidationError('Активная категория с таким названием уже существует.')


class DishForm(FlaskForm):
    name = StringField(
        'Название блюда',
        validators=[DataRequired(message='Укажите название блюда.'), Length(max=150)],
    )
    category_id = SelectField(
        'Категория',
        coerce=int,
        validators=[DataRequired(message='Выберите категорию.')],
    )
    description = TextAreaField('Описание', validators=[Optional(), Length(max=2000)])
    portion_size = DecimalField(
        'Масса/объём порции',
        places=2,
        validators=[
            InputRequired(message='Укажите массу порции.'),
            NumberRange(min=0.01, message='Масса порции должна быть больше нуля.'),
        ],
    )
    portion_unit = SelectField(
        'Единица измерения',
        choices=[(PORTION_UNIT_CHOICES[0], 'г'), (PORTION_UNIT_CHOICES[1], 'мл')],
    )
    price = DecimalField(
        'Цена, ₽',
        places=2,
        validators=[
            InputRequired(message='Укажите цену.'),
            NumberRange(min=0.01, message='Цена должна быть больше нуля.'),
        ],
    )
    is_available = BooleanField('В наличии', default=True)

    def set_category_choices(self, include_category_id=None):
        query = Category.query.filter_by(is_active=True)
        categories = query.order_by(Category.name).all()
        choices = [(c.id, c.name) for c in categories]

        if include_category_id is not None and include_category_id not in [c.id for c in categories]:
            archived = db.session.get(Category, include_category_id)
            if archived is not None:
                choices.insert(0, (archived.id, f'{archived.name} (архивная)'))

        self.category_id.choices = choices


class MenuDateForm(FlaskForm):
    menu_date = DateField('Дата меню', validators=[DataRequired(message='Укажите дату.')])

    def validate_menu_date(self, field):
        existing = Menu.query.filter_by(menu_date=field.data).first()
        if existing is not None:
            raise ValidationError('Меню на эту дату уже существует.')


class MenuItemForm(FlaskForm):
    dish_id = SelectField('Блюдо', coerce=int, validators=[DataRequired(message='Выберите блюдо.')])

    def set_dish_choices(self, menu_id):
        menu = db.session.get(Menu, menu_id)
        already_added = {item.dish_id for item in menu.items}
        dishes = Dish.query.order_by(Dish.name).all()
        choices = []
        for dish in dishes:
            if dish.id in already_added:
                continue
            label = f'{dish.name} — {dish.price} ₽'
            if not dish.is_available:
                label += ' (нет в наличии)'
            choices.append((dish.id, label))
        self.dish_id.choices = choices


class UserCreateForm(FlaskForm):
    username = StringField(
        'Логин',
        validators=[DataRequired(message='Укажите логин.'), Length(min=3, max=50)],
    )
    full_name = StringField(
        'Полное имя',
        validators=[DataRequired(message='Укажите имя сотрудника.'), Length(max=120)],
    )
    role_id = SelectField('Роль', coerce=int, validators=[DataRequired(message='Выберите роль.')])
    password = PasswordField(
        'Пароль',
        validators=[DataRequired(message='Укажите пароль.'), Length(min=6, message='Минимум 6 символов.')],
    )
    confirm_password = PasswordField(
        'Повторите пароль',
        validators=[EqualTo('password', message='Пароли не совпадают.')],
    )
    is_active_account = BooleanField('Учётная запись активна', default=True)

    def validate_username(self, field):
        exists = User.query.filter(db.func.lower(User.username) == field.data.strip().lower()).first()
        if exists is not None:
            raise ValidationError('Пользователь с таким логином уже существует.')


class UserEditForm(FlaskForm):
    full_name = StringField(
        'Полное имя',
        validators=[DataRequired(message='Укажите имя сотрудника.'), Length(max=120)],
    )
    role_id = SelectField('Роль', coerce=int, validators=[DataRequired(message='Выберите роль.')])
    is_active_account = BooleanField('Учётная запись активна')
    new_password = PasswordField(
        'Новый пароль',
        validators=[Optional(), Length(min=6, message='Минимум 6 символов.')],
    )
    confirm_password = PasswordField(
        'Повторите новый пароль',
        validators=[EqualTo('new_password', message='Пароли не совпадают.')],
    )


def role_choices():
    from app.models import Role

    return [(r.id, r.description or r.name) for r in Role.query.order_by(Role.name).all()]
