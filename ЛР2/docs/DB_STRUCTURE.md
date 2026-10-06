# Структура базы данных

СУБД: PostgreSQL 16. Схема управляется миграциями Alembic
(`migrations/versions/`), исходное описание — в `app/models.py`.
Актуальный список таблиц всегда можно посмотреть командой `\dt` в `psql`
или файлом `migrations/versions/0001_baseline_schema.py` — этот документ
описывает **что и почему**, а не дублирует SQL.

## Обзор таблиц

| Таблица       | Назначение                                              |
|---------------|----------------------------------------------------------|
| `roles`       | Справочник ролей: `admin`, `staff`                         |
| `users`       | Учётные записи сотрудников/администраторов                  |
| `categories`  | Категории блюд (Супы, Салаты, ...)                            |
| `dishes`      | Каталог блюд                                                    |
| `menus`       | Меню на конкретную дату (черновик/опубликовано)                  |
| `menu_items`  | Связь: какое блюдо в каком меню и в каком порядке                  |
| `audit_log`   | Журнал административных событий                                     |

## Диаграмма связей (текстовое представление)

```
roles 1───* users                     categories 1───* dishes
                                                            │
                                                            │ 1
                                                            │
                                                            *
                                       menus 1───* menu_items ──* dishes
                                                            
users 1───* audit_log (user_idнулевой — если пользователь позже удалён)
```

## Таблица `roles`

| Колонка       | Тип           | Ограничения        |
|---------------|---------------|---------------------|
| id            | integer PK    |                       |
| name          | varchar(20)   | NOT NULL, UNIQUE       |
| description   | varchar(200)  |                          |

Значения (`admin`, `staff`) заводятся не вручную, а прямо в базовой
миграции (`op.bulk_insert`), т.к. это часть схемы приложения, а не
данные, зависящие от окружения — код в `app/models.py` ссылается на эти
строки константами `ROLE_ADMIN`/`ROLE_STAFF`.

## Таблица `users`

| Колонка            | Тип            | Ограничения                          |
|---------------------|----------------|-----------------------------------------|
| id                   | integer PK     |                                            |
| username             | varchar(50)    | NOT NULL, UNIQUE, индекс                     |
| password_hash        | varchar(255)   | NOT NULL — хеш (werkzeug, PBKDF2), не пароль в открытом виде |
| full_name            | varchar(120)   | NOT NULL                                          |
| role_id              | integer FK → roles.id | NOT NULL                                    |
| is_active_account    | boolean        | NOT NULL, default true                              |
| created_at           | timestamp      | NOT NULL                                              |

`is_active_account`, а не физическое удаление — деактивированный
сотрудник не может войти (проверяется в `User.is_active`,
переопределяющем свойство `Flask-Login`), но история его действий в
`audit_log` остаётся читаемой.

## Таблица `categories`

| Колонка     | Тип           | Ограничения |
|-------------|---------------|--------------|
| id          | integer PK    |                |
| name        | varchar(100)  | NOT NULL         |
| is_active   | boolean       | NOT NULL, default true |
| created_at  | timestamp     | NOT NULL                 |

**Особенность:** вместо обычного `UNIQUE` на `name` используется
**частичный уникальный индекс**:

```sql
CREATE UNIQUE INDEX ix_categories_name_active_unique
    ON categories (name) WHERE is_active IS TRUE;
```

Это прямое требование п. 4.2.2 ТЗ — название не должно дублироваться
**в активном наборе**. Обычный `UNIQUE` запретил бы когда-либо снова
создать категорию с именем, которое раньше было архивировано; частичный
индекс проверяет уникальность только среди `is_active = true`, так что
архивная запись не блокирует новую с тем же названием.

## Таблица `dishes`

| Колонка       | Тип             | Ограничения |
|---------------|-----------------|--------------|
| id            | integer PK      |                |
| name          | varchar(150)    | NOT NULL, индекс |
| category_id   | integer FK → categories.id | NOT NULL |
| description   | text            | опционально      |
| portion_size  | numeric(8,2)    | NOT NULL, CHECK > 0 |
| portion_unit  | varchar(2)      | NOT NULL, CHECK IN ('g','ml') |
| price         | numeric(10,2)   | NOT NULL, CHECK > 0 |
| is_available  | boolean         | NOT NULL, default true |
| created_at    | timestamp       | NOT NULL |
| updated_at    | timestamp       | NOT NULL, обновляется автоматически |

**Почему `portion_unit`/статусы — `varchar` + `CHECK`, а не нативный
PostgreSQL `ENUM`:** нативный тип `ENUM` неудобно расширять — добавление
нового значения (`ALTER TYPE ... ADD VALUE`) в старых версиях PostgreSQL
нельзя выполнить внутри транзакции, что усложняет миграции. `varchar` с
`CHECK`-ограничением даёт ту же гарантию целостности на уровне БД, но
меняется обычным `ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT`
в одной миграции.

**Удаление блюда:** физического `DELETE` в приложении нет — снятие с
публикации выполняется переводом `is_available` в `false`
(`/admin/dishes/<id>/archive`). Это тот же флаг, что и «нет в наличии
сегодня»: в ТЗ у блюда только один булев признак наличия, поэтому он
сознательно используется в обеих ролях. Так исторические меню, уже
ссылающиеся на блюдо, не ломаются.

## Таблица `menus`

| Колонка       | Тип         | Ограничения |
|---------------|-------------|--------------|
| id            | integer PK  |                |
| menu_date     | date        | NOT NULL, UNIQUE — на одну дату одно меню |
| status        | varchar(10) | NOT NULL, CHECK IN ('draft','published') |
| created_at    | timestamp   | NOT NULL |
| updated_at    | timestamp   | NOT NULL |
| published_at  | timestamp   | NULL до публикации |

## Таблица `menu_items`

| Колонка        | Тип        | Ограничения |
|----------------|------------|--------------|
| id             | integer PK |                |
| menu_id        | integer FK → menus.id | NOT NULL |
| dish_id        | integer FK → dishes.id | NOT NULL |
| display_order  | integer    | NOT NULL, default 0 |

`UNIQUE(menu_id, dish_id)` — прямая реализация требования п. 4.2.4
«одно блюдо не должно появляться дважды в одном меню». При удалении
меню связанные `menu_items` удаляются каскадно (`cascade='all,
delete-orphan'` на уровне ORM); при удалении блюда из каталога
проектом не предусмотрено — блюда архивируются, а не удаляются
(см. выше), поэтому осиротевших `menu_items` в норме не возникает.

## Таблица `audit_log`

| Колонка      | Тип           | Ограничения |
|--------------|---------------|--------------|
| id           | integer PK    |                |
| user_id      | integer FK → users.id | NULL допустим |
| action       | varchar(20)   | NOT NULL: create / update / archive / restore / publish / unpublish |
| entity_type  | varchar(30)   | NOT NULL: category / dish / menu |
| entity_id    | integer       | NOT NULL |
| details      | varchar(255)  | человекочитаемая подробность (не обязательна) |
| created_at   | timestamp     | NOT NULL, индекс |

**Почему журнал «компактный» (п. 4.2.8 ТЗ):** фиксируются только
события уровня жизненного цикла сущности (создание/изменение/
архивирование/публикация), а не каждое добавление или удаление блюда
из пункта меню — построчная фиксация каждого клика быстро превращает
журнал в шум и лишает его практической ценности как инструмента
контроля. Список типов событий и сущностей закрытый — см. константы
`AUDIT_ACTION_*` в `app/models.py`.

## Наименование ограничений

Для всех индексов/constraint'ов используется единая naming convention
(`app/extensions.py`, `NAMING_CONVENTION`) — рекомендация из документации
Alembic. Без неё автоматически сгенерированные имена в разных версиях
SQLAlchemy/PostgreSQL могут отличаться, из-за чего последующая миграция,
меняющая или удаляющая constraint, не найдёт его по имени.

## Секреты

Строка подключения к БД и пароли — только в `.env` (не в репозитории,
см. `.gitignore`), в `.env.example` — только плейсхолдеры. Пароли
пользователей в БД хранятся как хеш (`werkzeug.security.
generate_password_hash`), не в открытом виде — п. 4.4.4 ТЗ.
