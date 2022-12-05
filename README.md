# Проект: Продуктовый помощник

## Макарьев Никита
[![Django-app workflow](https://github.com/NikitaMackariev/foodgram-project-react/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/NikitaMackariev/foodgram-project-react/actions/workflows/main.yml)

***
### Техническое описание. ###

Проект **Foodgram** является полноценным **«Продуктовым помощником»**, благодаря которому пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис **«Список покупок»** позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

В проекте реализован полноценный **«API»** сервис. На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список **«Избранное»**, а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

**Доступ к панели администратора:**

Электронная почта для входа: admin@yandex.ru

Пароль DomifU36

[Ссылка на размещенный проект на сервере Yandex.Cloud](http://158.160.9.220//)
***
### Пользовательские роли ###

  - Неавторизованные пользователи могут:
     - создать аккаунт;
     - просматривать рецепты на главной странице;
     - просматривать отдельные страницы рецептов;
     - просматривать страницы пользователей;
     - фильтровать рецепты по тегам.


  - Авторизованные пользователи могут:
     - входить в систему под своим логином и паролем;
     - выходить из системы (разлогиниваться);
     - менять свой пароль;
     - создавать/редактировать/удалять собственные рецепты;
     - просматривать рецепты на главной;  
     - просматривать страницы пользователей;
     - просматривать отдельные страницы рецептов;
     - фильтровать рецепты по тегам;
     - работать с персональным списком избранного: добавлять в него рецепты или удалять их, просматривать свою страницу избранных рецептов;
     - работать с персональным списком покупок: добавлять/удалять **любые** рецепты, выгружать файл с количеством необходимых ингридиентов для рецептов из списка покупок;
     - подписываться на публикации авторов рецептов и отменять подписку, просматривать свою страницу подписок.


  - Администратор может:
     - изменять пароль любого пользователя;
     - создавать/блокировать/удалять аккаунты пользователей;
     - редактировать/удалять **любые** рецепты;
     - добавлять/удалять/редактировать ингредиенты;
     - добавлять/удалять/редактировать теги.


***

### Алгоритм регистрации пользователей ###

1. Для добавления нового пользователя нужно отправить POST-запрос на эндпоинт /api/users/ с параметрами:
    - email;
    - username;
    - first_name;
    - last_name;
    - password.


2. Далее пользователь отправляет POST-запрос на эндпоинт /api/auth/token/login/ с параметрами:
    - password;
    - email.

В результате пользователь получает токен и может работать с API проекта, отправляя этот токен с каждым запросом.

***

### Шаблон наполнения env-файла ###


1. **DB_ENGINE=django.db.backends.postgresq**l - указываем, что работаем с postgresql.
2. **DB_NAME=postgres** - имя базы данных.
3. **POSTGRES_USER=postgres** - логин для подключения к базе данных.
4. **POSTGRES_PASSWORD=postgre** - пароль для подключения к БД (установите свой).
5. **DB_HOST=db** - название сервиса (контейнера).
6. **DB_PORT=5432** - порт для подключения к БД.

***

### Описание команд для запуска приложения в контейнерах ###
1. Перейдите в директорию **infra**, в которой распложен файл **docker-compose.yaml**:
```bash
cd infra/
```

2. Проверьте, что файл **docker-compose.yaml** находится в папке:
```bash
ls
```
```bash
docker-compose.yaml     nginx.conf
```
3. Запустите **docker-compose** командой:
```bash
docker-compose up -d
```
***


### Команды для заполнения базы данными. ###


Команды внутри контейнеров выполняют посредством подкоманды **docker-compose exe**.

Выполните миграции:

```bash
docker-compose exec web python manage.py migrate
```

Создать суперпользователя django:


```bash 
docker-compose exec web python manage.py createsuperuser
```


Придумайте логин (например, admin):

```bash
Username (leave blank to use 'user'):
```


Укажите почту:
```bash
Email address:
```


Придумайте пароль:

```bash
Password:
```


Повторите пароль:

```bash
Password (again):
```


Суперпользователь успешно создан:

```bash
Superuser created successfully.
```


Соберите статику:

```bash
docker-compose exec web python manage.py collectstatic --no-input
```

***

### Некоторые примеры запросов к API. ###

**Регистрация нового пользователя:**


эндпойнт:

```
/api/users/
```

HTTP-метод:

```
POST
```
Payload:
```python
{
    "email": "string",
    "username": "string",
    "first_name": "string",
    "last_name": "string",
    "password": "string"
}
```
Варианты ответов:
* удачное выполнение запроса: статус 201 
```python
{
    "email": "string",
    "id": "integer",
    "username": "string",
    "first_name": "string",
    "last_name": "string"
}
```

* запрос отклонен: статус 400 - отсутствует обязательное поле или оно некорректно
```python
{
  "field_name": [
    "Обязательное поле."
  ]
}
```

**Получение токена:**

эндпойнт:

```
/api/auth/token/login/
```

HTTP-метод:

```
POST
```
Payload:
```python
{
    "password": "string",
    "email": "string"
}
```
Варианты ответов:
* удачное выполнение запроса: статус 201
```python
{
    "token": "string"
}
```

* запрос отклонен: статус 400 - невозможно войти с предоставленными учетными данными
```python
{
    "non_field_errors": [
        "Невозможно войти с предоставленными учетными данными."
    ]
}
```

**Добавление нового рецепта**

Права доступа: **Авторизованный пользователь**.

эндпойнт:
```
/api/recipes/
```

HTTP-метод:
```
POST
```

Payload:
```python
{
    "ingredients": [
        {"id": "integer",
         "name": "string",
         "amount": "float"}
    ],
    "tags": [
    1,
    2
    ],
    "image": "string <binary>",
    "name": "string",
    "text": "string",
    "cooking_time": "integer"
}
```

Варианты ответов:
* удачное выполнение запроса: статус 201 
```python
{
    "id": "integer",
    "name": "string",
    "image": "string <binary>",
    "text": "string",
    "ingredients": [
        {
            "id": "integer",
            "name": "string",
            "amount": "float"
        }
    ],
    "tags": [
        {
            "id": "integer",
            "name": "string",
            "color": "string <HEX>",
            "slug": "string"
        }
    ],
    "cooking_time": "integer",
    "is_favorited": "bool",
    "is_in_shopping_cart": "bool",
    "author": {
        "first_name": "string",
        "username": "string",
        "last_name": "string",
        "email": "string",
        "password": "string",
        "id": integer,
        "is_subscribed": "bool"
    }
}
```

* запрос отклонен: статус 400 - отсутствует обязательное поле или оно некорректно
```python
{
    "field_name": [
    "Обязательное поле."
  ]
}
```

* запрос отклонен: статус 404 - объект не найден
```python
{
  "detail": "Страница не найдена."
}
```


**Получение списка ингредиентов:**

эндпойнт:

```
/api/ingredients/
```

HTTP-метод:

```
GET
```

в ответе:

```python
[
    {
    "id": 0,
    "name": "Капуста",
    "measurement_unit": "кг"
    }
]
```

**Обновление рецепта**

Права доступа: **Автор рецепта или администратор.**

эндпойнт:
```
/api/recipes/{id}/
```

HTTP-метод:
```
PATCH
```

Payload:
```python
{
    "ingredients": [
        {"id": "integer",
         "name": "string",
         "amount": "float"}
    ],
    "tags": [
    3,
    4
    ],
    "image": "string <binary>",
    "name": "string",
    "text": "string",
    "cooking_time": "integer"
}
```

Варианты ответов:
* удачное выполнение запроса: статус 200
```python
{
    "id": "integer",
    "name": "string",
    "image": "string <binary>",
    "text": "string",
    "ingredients": [
        {
            "id": "integer",
            "name": "string",
            "amount": "float"
        }
    ],
    "tags": [
        {
            "id": "integer",
            "name": "string",
            "color": "string <HEX>",
            "slug": "string"
        }
    ],
    "cooking_time": "integer",
    "is_favorited": "bool",
    "is_in_shopping_cart": "bool",
    "author": {
        "first_name": "string",
        "username": "string",
        "last_name": "string",
        "email": "string",
        "password": "string",
        "id": integer,
        "is_subscribed": "bool"
}
```

* запрос отклонен: статус 400 - отсутствует обязательное поле или оно некорректно
```python
{
  "field_name": [
    "Обязательное поле."
  ]
}
```

* запрос отклонен: статус 401 - необходим токен
```python
{
  "detail": "Учетные данные не были предоставлены."
}
```

* запрос отклонен: статус 403 - нет прав доступа
```python
{
  "detail": "Нет прав доступа."
}
```

* запрос отклонен: статус 404 - рецепт не найден
```python
{
  "detail": "Рецепт не найден."
}
```
