# **hw05_final**
### **Описание**
Социальная сеть блогеров. Учебный проект.

- Подписки на пользователей.
- Просмотр, создание, изменение и удаление записей.
- Просмотр и создание групп.
- Возможность добавления, редактирования, удаления своих комментариев и просмотр чужих.
- Подключены пагинация, кеширование, авторизация пользователя. Неавторизованному пользователю доступно только чтение.
- Код покрытыт тестами.

### **Стек**
![python version](https://img.shields.io/badge/Python-3.7-green)
![django version](https://img.shields.io/badge/Django-2.2-green)
![pytest version](https://img.shields.io/badge/pytest-4.4-green)
![sorl-thumbnail version](https://img.shields.io/badge/thumbnail-12.7-green)

### **Запуск проекта**

1. Клонируйте репозиторий:

```
git clone https://github.com/TsekovDavid/hw05_final.git
```

2. Установите и активируйте виртуальное окружение:
```
python3 -m venv venv
``` 
```
. venv/bin/activate
```

3. Установите зависимости:
```
pip3 install -r requirements.txt
```

4. В папке с файлом manage.py выполните миграции и запустите сервер:
```
python3 manage.py migrate
```
```
python3 manage.py runserver
```

* проект доступен по адресу: ```http://127.0.0.1:8000```
### **Эндпоинты:**
* ```posts/``` - Отображение постов и публикаций (_GET, POST_);
* ```posts/{id}``` - Получение, изменение, удаление поста с соответствующим **id** (_GET, PUT, PATCH, DELETE_);
* ```posts/{post_id}/comments/``` - Получение комментариев к посту с соответствующим **post_id** и публикация новых комментариев(_GET, POST_);
* ```posts/{post_id}/comments/{id}``` - Получение, изменение, удаление комментария с соответствующим **id** к посту с соответствующим **post_id** (_GET, PUT, PATCH, DELETE_);
* ```posts/groups/``` - Получение описания зарегестрированных сообществ (_GET_);
* ```posts/groups/{id}/``` - Получение описания сообщества с соответствующим **id** (_GET_);
* ```posts/follow/``` - Получение информации о подписках текущего пользователя, создание новой подписки на пользователя (_GET, POST_).<br/>
