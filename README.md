# 📖 Quotes Website - Случайные цитаты

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-4.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Django-приложение для отображения случайных цитат из фильмов и книг с системой оценок и возможностью добавления новых цитат.

## ✨ Возможности

- 🎲 **Случайные цитаты** - При каждом обновлении показывается случайная цитата
- ⚖️ **Система весов** - Цитаты с большим весом показываются чаще
- 👍👎 **Оценки** - Система лайков и дизлайков
- 📊 **Топ-10** - Страница с самыми популярными цитатами
- ➕ **Добавление** - Возможность добавлять новые цитаты
- 👤 **Аутентификация** - Регистрация и вход для оценки цитат
- 🎨 **Красивый дизайн** - Анимированный фон и современный интерфейс

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.8+
- Django 4.0+
- SQLite (по умолчанию)

### Установка

1. **Клонируй репозиторий**
```bash
git clone https://github.com/yourusername/quotes_website.git
cd quotes_website

## 🏗 Структура проекта

```text
quotes_website/
├── quotes_website/                 # Корневая директория проекта
│   ├── quotes/                     # Основное приложение
│   │   ├── catalog/               # Подмодуль каталога
│   │   │   ├── __pycache__/
│   │   │   ├── templates/myapp/   # Шаблоны приложения
│   │   │   │   ├── login.html
│   │   │   │   ├── quote.html
│   │   │   │   ├── register.html
│   │   │   │   └── top_quotes.html
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── apps.py
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   ├── tests.py
│   │   │   ├── urls.py
│   │   │   └── views.py
│   │   └── quotes/                # Настройки проекта
│   │       ├── __pycache__/
│   │       ├── __init__.py
│   │       ├── asgi.py
│   │       ├── settings.py
│   │       ├── urls.py
│   │       └── wsgi.py
│   ├── static/                    # Статические файлы
│   │   └── myapp/
│   │       ├── image/            # Изображения
│   │       └── style.css         # Стили CSS
│   ├── staticfiles/              # Собранные статические файлы
│   │   ├── admin/               # Статика админки Django
│   │   │   ├── css/
│   │   │   ├── img/
│   │   │   └── js/
│   │   └── myapp/               # Статика приложения
│   │       ├── image/
│   │       └── style.css
│   ├── templates/registration/   # Шаблоны аутентификации
│   │   └── login.html
│   ├── __init__.py
│   ├── db.sqlite3               # База данных SQLite
│   ├── manage.py               # Управляющий скрипт Django
│   ├── venv/                   # Виртуальное окружение
│   ├── requirements.dev.txt    # Зависимости для разработки
│   └── requirements.txt        # Основные зависимости
└── README.md                   # Документация проекта
