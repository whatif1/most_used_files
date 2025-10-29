from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pathlib import Path
import logging
import operator
from sqlalchemy import select, func, extract, or_, and_, update, delete
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import RelationshipProperty, Load, InstrumentedAttribute, joinedload

BASE_DIR = Path(__file__).resolve().parent.parent

# Определяем абсолютный путь к корневой папке проекта. Path(__file__) -> путь к текущему файлу (database_engine.py).resolve() -> делает путь абсолютным .parent -> родительская папка (папка 'database') .parent -> родительская папка родительской папки (корень проекта!)
DATABASE_FILE_PATH = BASE_DIR / "my_db.db"  # - my_db.db - название файла базы данных.

# адрес шаблона БД sqlite3 - 'sqlite+aiosqlite:///./название_базы_данных'
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_FILE_PATH}"

# двигатель для асинхронной sqlite3
engine = create_async_engine(url=SQLALCHEMY_DATABASE_URL, echo=False, pool_size=5, max_overflow=3)

# создаем генератор сессий.
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# создаем класс для создания всех таблиц и миграций. Это будет родительским классом для всех наших будущих моделей.
class Base(DeclarativeBase):
    pass


class BaseDao:
    model = None

    OPERATORS = {
        "exact": operator.eq,  # равно ==. Точное совпадение с учетом регистра или пои цифрам
        "iexact": lambda column, value: column.ilike(value),  # Точное совпадение без учета регистра в строках
        "contains": lambda column, value: column.contains(value),  # искомое значение в строке с учетом регистра
        # "icontains": lambda column, value: column.icontains(value), # искомое значение содержится в строке без учеата регистра
        "icontains": lambda column, value: func.lower(column).contains(value.lower()),
        # искомое значение содержится в строке без учета регистра
        'gt': operator.gt,  # Больше (>)
        'gte': operator.ge,  # Больше или равно (>=)
        'lt': operator.lt,  # Меньше (<)
        'lte': operator.le,  # Меньше или равно (<=)
        'in': lambda column, value: column.in_(value),
        # Проверяет, содержится ли значение в указанном списке значений. Ожидает [1, 5, 10, 15]
        "range": lambda column, value: column.between(value[0], value[1]),  # проверяет, находится ли указанное
        # значение между двумя значениями. Ожидает [10, 20].
        "ne": operator.ne,  # "не равно" (!=)
        "is_null": lambda column, value: column.is_(None) if value else column.is_not(None),  # проверка на Null
        # Начинается с
        "startswith": lambda column, value: column.startswith(value),
        "istartswith": lambda column, value: column.istartswith(value),
        # Заканчивается на
        "endswith": lambda column, value: column.endswith(value),
        "iendswith": lambda column, value: column.iendswith(value),

        # Фильтры по дате/времени
        "date": lambda column, value: func.date(column) == value,
        "year": lambda column, value: extract('year', column) == value,
        "month": lambda column, value: extract('month', column) == value,
        "day": lambda column, value: extract('day', column) == value,

    }



    class BaseDao:
    model = None

    OPERATORS = {
        "exact": operator.eq,  # равно ==. Точное совпадение с учетом регистра или пои цифрам
        "iexact": lambda column, value: column.ilike(value),  # Точное совпадение без учета регистра в строках
        "contains": lambda column, value: column.contains(value),  # искомое значение в строке с учетом регистра
        # "icontains": lambda column, value: column.icontains(value), # искомое значение содержится в строке без учеата регистра
        "icontains": lambda column, value: func.lower(column).contains(value.lower()),
        # искомое значение содержится в строке без учета регистра
        'gt': operator.gt,  # Больше (>)
        'gte': operator.ge,  # Больше или равно (>=)
        'lt': operator.lt,  # Меньше (<)
        'lte': operator.le,  # Меньше или равно (<=)
        'in': lambda column, value: column.in_(value),
        # Проверяет, содержится ли значение в указанном списке значений. Ожидает [1, 5, 10, 15]
        "range": lambda column, value: column.between(value[0], value[1]),  # проверяет, находится ли указанное
        # значение между двумя значениями. Ожидает [10, 20].
        "ne": operator.ne,  # "не равно" (!=)
        "is_null": lambda column, value: column.is_(None) if value else column.is_not(None),  # проверка на Null
        # Начинается с
        "startswith": lambda column, value: column.startswith(value),
        "istartswith": lambda column, value: column.istartswith(value),
        # Заканчивается на
        "endswith": lambda column, value: column.endswith(value),
        "iendswith": lambda column, value: column.iendswith(value),

        # Фильтры по дате/времени
        "date": lambda column, value: func.date(column) == value,
        "year": lambda column, value: extract('year', column) == value,
        "month": lambda column, value: extract('month', column) == value,
        "day": lambda column, value: extract('day', column) == value,

    }

    @classmethod
    async def universal_find_method(
            cls,
            *,
            session: AsyncSession,
            simple_filters: dict = None,
            join_only_simple_filters_with_or: bool = False,
            load_relationships: list = None,
            search_in_many_to_many_field_using_and: dict = None,
            columns_to_select: list = None,
            page: int = None,
            size: int = None,
            order_by: list = None,
    ):
        """
        Пример использования:

        :param session - обязательный параметр для каждого запроса в fastapi чтобы можно было делать много независимых
        запросов в рамках одной сессии:

        # Поиск по обычным фильтрам. Поиск по датам можно совмещать
        :param simple_filters:
        simple_filters={"username__icontains": "fo", "published_at__year": 2020},
        :param join_only_simple_filters_with_or: - то же самое, что и simple_filters, только при помощи or


        # or или and только для simple filter
        join_only_simple_filters_with_or=False,

        :param search_in_many_to_many_field_using_and:
        # только для поиска по many-to-many или one-to-many при помощи И. Используется только для поиска по И (при помощи ИЛИ происходит по умолчанию).
        search_in_many_to_many_field_using_and={"skills__id": [5, 2]},

        :param load_relationships:
        # load_relationships используется только для полей relationship для решения проблемы n+1.
        load_relationships=[User.skills], ['user__skills'], selectinload(User.skills), joinedload(Post.user), selectinload(User.skills).joinedload(Post.user)
        Всегда на 100% использовать selectinload(User.skills) - для загрузки 1 ко многим (если мы хотим получить список данных), joinedload(Post.user) - для загрузки 1 к 1 - если ожидаем получить 1 значение либо дублировать, чтобы сначала получить много значений, а потом для каждого из них 1 нужное (либо наоборот, сначала получить 1, а потом для него много).
        Данный метод теперь может принимать все виды связей, которые передаются в load_relationships для загрузки связанных данных. Теперь в него можно передавать не только [posts__comments] и [User.posts], но и [selectinload(User.posts)] и сложные опции [selectinload(Post.likes).joinedload(Like.user)] - Эта проверка говорит: "Если разработчик уже сам позаботился и передал нам полностью готовую, сложную инструкцию по загрузке, не надо ничего придумывать. Просто возьмем ее как есть и используем".
        Взаимоисключающее по отношению к columns_to_select

        :param columns_to_select:
        # для выбора данных в виде списка только из указанных полей. Аналог Django.values_list(flat=True). Взаимоисключающее по отношению к load_relationships
        columns_to_select
        usernames = await UserDao.universal_find_method(columns_to_select=[User.username])
        # Вернет: ['Alex', 'Bob', 'Charlie']

        :param page: номер страницы. Если указать page - будет делаться 2 запроса в БД. Используется только в pagination методе и вернет не список ORM, словарь {'items': [food], 'total_pages': 2, 'current_page': 1}, где ORM содержится в items.
        :param size: количество записей на странице. Используется только в pagination методе.


        :param order_by: Список строк для сортировки. Можно использовать - как в Django для обратной сортировки.

        ВАЖНО: Параметры `columns_to_select` и `load_relationships` являются взаимоисключающими.
        `load_relationships` предназначен для загрузки связанных ОБЪЕКТОВ вместе с основным,
        в то время как `columns_to_select` используется для получения "сырых" данных из конкретных столбцов.
        Их совместное использование не имеет смысла.
        """

        if columns_to_select:
            if load_relationships:
                logging.warning(
                    "`columns_to_select` и `load_relationships` использованы вместе. `load_relationships` будет проигнорирован.")
            query = select(*columns_to_select)
        else:
            query = select(cls.model)

        if simple_filters:
            conditions = []
            for key, value in simple_filters.items():
                field_parts = key.split("__")
                operator_name = "exact"
                if len(field_parts) > 1 and field_parts[-1] in cls.OPERATORS:
                    operator_name = field_parts.pop()
                current_model = cls.model
                column_obj = None
                path_query = query
                for index, part_name in enumerate(field_parts):
                    try:
                        attr = getattr(current_model, part_name)
                    except AttributeError:
                        raise AttributeError(
                            f"Модель '{current_model.__name__}' не имеет атрибута '{part_name}' для фильтра '{key}'")
                    if index < len(field_parts) - 1:
                        if not isinstance(getattr(attr, 'property', None), RelationshipProperty):
                            raise TypeError(
                                f"Атрибут '{part_name}' в пути '{key}' не является связью relationship.")
                        path_query = path_query.join(attr)
                        current_model = attr.entity.class_
                    else:
                        column_obj = attr
                query = path_query
                chosen_operator = cls.OPERATORS[operator_name]
                conditions.append(chosen_operator(column_obj, value))
            if conditions:
                join_logic = or_ if join_only_simple_filters_with_or else and_
                query = query.where(join_logic(*conditions))

        if search_in_many_to_many_field_using_and:
            for key, values in search_in_many_to_many_field_using_and.items():
                if not isinstance(values, (list, set)) or not values: continue
                try:
                    relationship_name, field_name = key.rsplit('__', 1)
                except ValueError:
                    raise ValueError(f"Неверный формат ключа: '{key}'. Ожидается 'relationship__fieldname'.")
                try:
                    relationship_attr = getattr(cls.model, relationship_name)
                    related_model = relationship_attr.property.mapper.class_
                    field_attr = getattr(related_model, field_name)
                except AttributeError:
                    raise AttributeError(f"Не найдены атрибуты для ключа '{key}'")
                for v in values:
                    query = query.where(relationship_attr.any(field_attr == v))

        if order_by:
            ordering_clauses = []
            for field in order_by:
                if field.startswith('-'):
                    # Сортировка по убыванию
                    column_name = field[1:]
                    column_attr = getattr(cls.model, column_name, None)
                    if column_attr:
                        ordering_clauses.append(column_attr.desc())
                else:
                    # Сортировка по возрастанию
                    column_attr = getattr(cls.model, field, None)
                    if column_attr:
                        ordering_clauses.append(column_attr.asc())

            if ordering_clauses:
                query = query.order_by(*ordering_clauses)

        if page is not None:
            # РЕЖИМ ПАГИНАЦИИ

            # 1. Запрос COUNT, который использует уже построенные фильтры и join'ы
            count_query = select(func.count(cls.model.id).distinct()).select_from(*query.get_final_froms())

            if query.whereclause is not None:
                count_query = count_query.where(query.whereclause)

            total_count_result = await session.execute(count_query)
            total_count = total_count_result.scalar_one()

            # это готовый словарь, если есть пагинация - {'items': [food], 'total_pages': 2, 'current_page': 1}.
            if total_count == 0:
                return {"items": [], "total_pages": 0, "current_page": page}

            # 2. Основной запрос с LIMIT/OFFSET
            total_pages = math.ceil(total_count / size)
            offset = (page - 1) * size
            final_query = query.limit(size).offset(offset)

            # ВАША ЛОГИКА ЗАГРУЗКИ СВЯЗЕЙ ПРИМЕНЯЕТСЯ ЗДЕСЬ (1-В-1)
            if load_relationships and not columns_to_select:
                load_options = []
                for item in load_relationships:
                    option = None
                    if isinstance(item, Load):
                        option = item
                    elif isinstance(item, InstrumentedAttribute):
                        option = joinedload(item)
                    elif isinstance(item, str):
                        current_model = cls.model
                        option_chain = None
                        parts = item.split('__')
                        for part in parts:
                            attr = getattr(current_model, part)
                            if option_chain is None:
                                option_chain = joinedload(attr)
                            else:
                                option_chain = option_chain.joinedload(attr)
                            current_model = attr.entity.class_
                        option = option_chain
                    if option:
                        load_options.append(option)
                if load_options:
                    final_query = final_query.options(*load_options)

            # ВАША ЛОГИКА ВЫПОЛНЕНИЯ И ВОЗВРАТА РЕЗУЛЬТАТА (1-В-1)
            final_query = final_query.distinct()
            result = await session.execute(final_query)

            if columns_to_select:
                items = result.scalars().all() if len(columns_to_select) == 1 else result.mappings().all()
            else:
                items = result.unique().scalars().all()

            return {"items": items, "total_pages": total_pages, "current_page": page}

        else:
            # ОБЫЧНЫЙ РЕЖИМ (ВАШ ОРИГИНАЛЬНЫЙ КОД 1-В-1)

            # ВАША ЛОГИКА ЗАГРУЗКИ СВЯЗЕЙ (1-В-1)
            if load_relationships and not columns_to_select:
                load_options = []
                for item in load_relationships:
                    option = None
                    if isinstance(item, Load):
                        option = item
                    elif isinstance(item, InstrumentedAttribute):
                        option = joinedload(item)
                    elif isinstance(item, str):
                        current_model = cls.model
                        option_chain = None
                        parts = item.split('__')
                        for part in parts:
                            attr = getattr(current_model, part)
                            if option_chain is None:
                                option_chain = joinedload(attr)
                            else:
                                option_chain = option_chain.joinedload(attr)
                            current_model = attr.entity.class_
                        option = option_chain
                    if option:
                        load_options.append(option)
                if load_options:
                    query = query.options(*load_options)

            # ВАША ЛОГИКА ВЫПОЛНЕНИЯ И ВОЗВРАТА РЕЗУЛЬТАТА (1-В-1)
            query = query.distinct()
            result = await session.execute(query)

            if columns_to_select:
                if len(columns_to_select) == 1:
                    return result.scalars().all()
                else:
                    return result.mappings().all()
            else:
                return result.unique().scalars().all()  

    @classmethod
    async def get_all_objects(cls, *, session: AsyncSession, load_relationships: list = None,
                              columns_to_select: list = None):
        """
        Получает все объекты модели.

        :param session - обязательный параметр для каждого запроса в fastapi чтобы можно было делать много независимых
        запросов в рамках одной сессии:
        :param load_relationships: Список для "жадной" загрузки связей.
                                   Пример: get_all_objects(load_relationships=[User.posts, User.skills])
        :param columns_to_select: Список полей для выборки. Если указан, `load_relationships` игнорируются.
                                  Пример: news_data = await NewsDao.get_all_objects(columns_to_select=[News.id, News.title])
                                  # news_data будет -> [{'id': 1, 'title': '...'}, {'id': 2, 'title': '...'}]
        :return: Список полных объектов, либо список словарей/значений, если указан `columns_to_select`.
        """
        return await cls.universal_find_method(session=session, load_relationships=load_relationships,
                                               columns_to_select=columns_to_select)

    @classmethod
    async def get_one_object_by_any_field_or_none(cls, *, session: AsyncSession, load_relationships: list = None,
                                                  columns_to_select: list = None, **data):
        """
            Находит один объект по точным совпадениям полей или возвращает None.

        :param session - обязательный параметр для каждого запроса в fastapi чтобы можно было делать много независимых
        запросов в рамках одной сессии:
        :param load_relationships: Список для "жадной" загрузки связей.
        :param columns_to_select: Список полей для выборки. Если указан, вернет словарь или одно значение.
        :param data: Именованные аргументы для фильтрации по точному совпадению.
                     Пример: news_data = await NewsDao.get_one_object_by_any_field_or_none(id=5, columns_to_select=[News.id, News.title])
                     вернет: # news_data будет -> {'id': 5, 'title': 'Какой-то заголовок'} или None
        :return: Один объект модели, словарь, одно значение или None.

        """
        # Преобразуем и вызываем универсальный метод
        filters = {f"{key}__exact": value for key, value in data.items()}
        result_list = await cls.universal_find_method(session=session, load_relationships=load_relationships,
                                                      simple_filters=filters, columns_to_select=columns_to_select)
        # Добавляем логику "один или ноль"
        if result_list:
            return result_list[0]
        return None

    @classmethod
    async def insert_data(cls, *, session: AsyncSession, **data):
        new_object = cls.model(**data)
        session.add(new_object)
        await session.flush()  # Используем flush, чтобы получить ID и другие default-значения от БД
        await session.refresh(new_object)  # Обновляем объект данными из БД
        return new_object

    # для записи данных, которы включат поля many to many
    @classmethod
    async def create_with_m2m(cls, *, session: AsyncSession, main_data: dict, m2m_data: dict):
        """
        Универсальный метод для создания объекта со связями "многие-ко-многим".

        :param session - обязательный параметр для каждого запроса в fastapi чтобы можно было делать много независимых
        запросов в рамках одной сессии:

        :param main_data: Словарь с данными для основного объекта (например, {'username': 'John'}).
        :param m2m_data: Словарь, где ключ - имя M2M поля, а значение - список ID.
                         (например, {'skills': [1, 5], 'interests': [10, 12]})

        для работы этого метода нужно создать 2 таблицы и связать их при помощи ассоциативной таблиццы

        # Таблица ассоциации для связи Many-to-Many. Создаем объект таблицы напрямую, используя конструктор Table.
        user_skills_table = Table(
            # 'user_skills' — имя таблицы, которое будет создано в базе данных.
            'user_skills',
            # Base.metadata — это "реестр", где SQLAlchemy хранит информацию обо всех таблицах, связанных с этим базовым классом. Мы говорим: "эта таблица является частью нашей схемы данных".
            Base.metadata,
            # Определяем первую колонку в этой таблице.
            Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=True, primary_key=True),
            # Определяем вторую колонку в этой таблице.
            Column('skill_id', Integer, ForeignKey('skills.id', ondelete="CASCADE"), nullable=True, primary_key=True)
        )


        # это many to many таблица. Т.е. таких значений у человека может быть много
        class Skill(Base):
            __tablename__ = "skills"
            id = Column(Integer, primary_key=True, index=True)
            name = Column(String, unique=True, nullable=False)

            # Отношение для обратной связи (какие пользователи имеют этот скилл). Это поле many to many.
            users = relationship(
                "User",
                secondary=user_skills_table,
                back_populates="skills",
                lazy='raise_on_sql'
            )

            def __repr__(self):
                return f"{self.name}"


        class SkillDao(BaseDao):
            model = Skill


        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True, index=True)
            username = Column(String, unique=True, nullable=False)

            # Новое поле relationship. Это полу many to many
            skills = relationship(
                "Skill",
                secondary=user_skills_table,
                back_populates="users",
                lazy="raise_on_sql"  # Оптимизация для загрузки скиллов вместе с пользователем
            )

            def __repr__(self):
                return f"{self.id}"


        class UserDao(BaseDao):
            model = User


        так же нужно создать эндпоинт для получения всех значений из таблицы mtm и метод для записи данных в бд

        @main_api_router.get(path="/get_skills_options", name="get_skills_options")
        async def get_skills_options():
            # Теперь мы берем опции из таблицы Skill, а не из Enum. Предполагается, что у вас есть DAO для модели Skill
            all_skills: list[Skill] = await SkillDao.get_all_objects()
            # Возвращаем ID в качестве value, так как будем работать с ним
            return [{"value": skill.id, "label": skill.name} for skill in all_skills]

        # [
        #   {
        #     "value": 1,
        #     "label": "agility"
        #   },
        #   {
        #     "value": 2,
        #     "label": "problem solver "
        #   },
        #   {
        #     "value": 3,
        #     "label": "wit"
        #   }
        # ]


        @main_api_router.post(path="/create_user", name="create_user")
        async def create_user(data: UserRegistrationScheme):

            try:
                # 1. это данные для обычных полей. Не для many to many
                main_user_data = {
                    "username": data.username
                }
                m2m_relations_data = {
                    "skills": data.skills  # 'это список значений с индексами из таблицы many to many. m2m_relations_data = {'skills': [2, 3]}
                    # Если появятся другие поля many to many, просто добавляете их сюда:
                    # "interests": data.interests,
                    # "roles": data.roles
                }

                # 2. Вызываем ОДИН универсальный метод из DAO
                new_user = await UserDao.create_with_m2m(
                    main_data=main_user_data,
                    m2m_data=m2m_relations_data
                )

                # 3. Возвращаем успешный ответ
                return {
                    "id": new_user.id,
                    "username": new_user.username,
                    "skills_count": len(new_user.skills),  # Можем даже посчитать связанные скиллы
                    "message": "Пользователь успешно создан со всеми связями."
                }

            except ValueError as e:
                # Эта ошибка прилетит из DAO, если какие-то ID не будут найдены
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                # Ловим любые другие ошибки (например, дубликат username)
                # Здесь можно добавить логирование ошибки `e`
                raise HTTPException(status_code=500, detail="Произошла внутренняя ошибка сервера.")
        """

        found_m2m_objects = {}

        for field_name, ids in m2m_data.items():
            if not ids:
                continue
            many_to_many_field = getattr(cls.model, field_name)
            related_model = many_to_many_field.property.mapper.class_
            query = select(related_model).where(related_model.id.in_(ids))
            result = await session.execute(query)
            objects_to_link = result.scalars().all()

            if len(objects_to_link) != len(set(ids)):
                raise ValueError(f"Не найдены некоторые записи для поля '{field_name}'")
            found_m2m_objects[field_name] = objects_to_link

        new_object = cls.model(**main_data)
        for field_name, objects in found_m2m_objects.items():
            getattr(new_object, field_name).extend(objects)

        session.add(new_object)
        await session.flush()
        await session.refresh(new_object)
        return new_object

    @classmethod
    async def update_data(cls, *, session: AsyncSession, clauses: list, **data):
        if not clauses: raise ValueError("Необходимо указать условия (clauses) для обновления.")
        stmt = update(cls.model).where(*clauses).values(**data).returning(cls.model)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def save(cls, instance_obj, *, session: AsyncSession):
        """
        Сохраняет экземпляр объекта.
        Выполняет INSERT для нового объекта (без primary key)
        или UPDATE для существующего.
        """
        """Сохраняет экземпляр: INSERT для нового, UPDATE для существующего."""
        try:
            # session.merge() идеально подходит для "сохранения":
            # он сам определяет, нужно делать INSERT или UPDATE.
            merged_object = await session.merge(instance_obj)
            await session.flush()
            # refresh не всегда нужен после merge, но он гарантирует,
            # что в объекте будут самые свежие данные из БД (например, default значения)
            await session.refresh(merged_object)
            return merged_object
        except (IntegrityError, DatabaseError) as e:
            logging.error(f"Save failed due to database error: {e}")
            # Передаем ошибку выше, чтобы сработал rollback в зависимости
            raise

    @classmethod
    async def delete_data(cls, *, session: AsyncSession, clauses: list):
        if not clauses:
            raise ValueError("Необходимо указать условия (clauses) для удаления.")
        stmt = delete(cls.model).where(*clauses)
        await session.execute(stmt)


# пример fk * - foreign key *
# class Author(Base):
#     __tablename__ = "authors"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(length=500), nullable=True)
#     author_book_relationship = relationship("Book", back_populates="book_author_relationship", lazy="raise_on_sql")
#     created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate= func.now())
#
#     def __repr__(self):
#         return f"{self.name}"
#
#
# class AuthorDao(BaseDao):
#     model = Author
#
#
# class Publisher(Base):
#     __tablename__ = "publishers"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(length=500), nullable=True)
#     publisher_book_relationship = relationship("Book", back_populates="book_publisher_relationship", lazy="raise_on_sql")
#     created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate= func.now())
#
#     def __repr__(self):
#         return f"{self.name}"
#
#
# class PublisherDao(BaseDao):
#     model = Publisher
#


# class UserDao(BaseDao):
#     model = User
#
#
# class LikeDao(BaseDao):
#     model = Like
#
#
# class PostDao(BaseDao):
#     model = Post


# теперь тут же создаем самый главный класс, через который будет осуществляться любое взаимодействие с базой данных. Т.е. все, что мы делаем с базой данных - будет проходить через этот класс, так как именно тут будут создаваться сессия


# теперь любое взаимодействие с БД будет осуществляться через этот класс
class MyUniversaSessionClass:
    def __init__(self):
        self.session_factory = async_session_maker

    # Начинает транзакцию. Открывает сессию, готовит DAO к работе
    async def __aenter__(self):
        self.session: AsyncSession = self.session_factory()

        # Здесь регистрируем DAO. Они станут доступны через db.user_dao, uow.post_dao. Теперь в одной сессии будут данные о всех DAO
        # self.user_dao: UserDao = self._create_dao_proxy(UserDao, self.session)
        # self.post_dao: PostDao = self._create_dao_proxy(PostDao, self.session)
        # self.like_dao: LikeDao = self._create_dao_proxy(LikeDao, self.session)

        return self

    # Завершает транзакцию. Успешно? Делает commit. Произошла ошибка? Делает rollback. В любом случае закрывает сессию, чтобы не было утечек.
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

    # данный метод сам всегда будет передавать сессию. Нам нигде этого делать не надо.
    def _create_dao_proxy(self, dao_class, session):
        class DaoProxy:
            # 1. Находим оригинальный метод (например, get_all_objects)
            def __getattr__(self, name):
                original_method = getattr(dao_class, name)

                # 2. Создаем "обертку" для него
                def proxy_method(*args, **kwargs):
                    # 3. ВОТ КЛЮЧЕВОЙ МОМЕНТ!
                    # Вызываем оригинальный метод, но ВСЕГДА ДОБАВЛЯЕМ session=session
                    return original_method(session=session, *args, **kwargs)

                # 4. Возвращаем эту "обертку"
                return proxy_method

        return DaoProxy()









































# если мы в fastapi - создать в этом же файле данную функцию, так как в fastapi нельзя передвать функции в качестве аргументов. Нам нужно создать функцию, которую будет передвать в depends для работы с базой данных. Если работаем в python - эту фнкцию использовать не нужно.


async def universal_fastapi_db_transaction() -> MyUniversaSessionClass:
    """
    Эта зависимость FastAPI создает транзакцию для каждого запроса.
    """

    # Это "фабрика" или "менеджер" для работы с базой данных (для всего проекта), который будет активирован когда его будут использовать в async with. После этого      он получает все таблицы из класса MyUniversaSessionClass и создаст одну общую сессию для всех таблиц для удобной работы с ними. Нам всегда нужна будет             функция-последник для работы с данным методом (как в fastapi, python и везде); именно в этой функции мы активируем данную фабрику при помощи async with.
    my_universal_session = MyUniversaSessionClass()
    
    async with my_universal_session as db:
        yield db





# fastapi_main_api.py - в fastapi использовать так


@main_api_router.get(path="/get_one_post/{post_id}", name="get_one_post", response_model=PostBase)
async def get_one_post(request: Request, post_id: str,

db: MyUniversaSessionClass = Depends(universal_fastapi_db_transaction)):

    found_post: Post = await db.post_dao.get_one_object_by_any_field_or_none(
        load_relationships=[joinedload(Post.user), selectinload(Post.likes)], id=post_id)

    if not found_post:
        raise HTTPException(status_code=404, detail=f"Пост с ID '{post_id}' не найден.")
    ready_found_post = PostBase.model_validate(obj=found_post, context={"base_url": request.base_url})
    return ready_found_post






































































































# если мы в python.py, pyqt - создать функцию-посредник в отдельном файле чтобы к ней обращаться во всем проекте.

import asyncio
from sqlalchemy.orm import selectinload, joinedload
from database.database_engine import Post, User, Like, UserDao, LikeDao, PostDao, MyUniversaSessionClass
from functools import wraps


def run_in_one_transaction(db_function):
    """
    Декоратор, который выполняет асинхронную функцию внутри одной транзакции.
    Он использует ваш `my_universal_session` для управления сессией.
    """
    @wraps(db_function)
    async def wrapper(*args, **kwargs):
        my_universal_session = MyUniversaSessionClass()
        async with my_universal_session as session:
            # Передаем менеджер `session` в декорируемую функцию в качестве первого аргумента. Вручную теперь сессию передавать не нужно
            result = await db_function(session, *args, **kwargs)
            return result
    return wrapper


@run_in_one_transaction
async def find_user(db: MyUniversaSessionClass, *args, **kwargs):
    result: User = await db.user_dao.get_one_object_by_any_field_or_none(*args, **kwargs)
    return result


@run_in_one_transaction
async def change_user(db: MyUniversaSessionClass, old_username, new_username, *args, **kwargs):
    found_user = await db.user_dao.get_one_object_by_any_field_or_none(first_name=old_username)
    found_user.first_name = new_username
    await db.user_dao.save(found_user)
    return found_user


async def main():
    # В качестве db_function используем функцию для работы с базой данных, а далее передаем аргументы для той функции.
    found_use: User = await find_user(first_name="foma")
    changed_user = await change_user(old_username="josh", new_username='bill')
    print(found_use, changed_user)


if __name__ == "__main__":
    asyncio.run(main())


