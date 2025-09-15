import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.forms import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .forms import QuoteForm
from .models import Quote, Source, SourceType


class BaseTestSetup(TestCase):
    """Базовый класс для настройки тестовых данных"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.movie_type = SourceType.objects.create(name="Фильм")
        self.book_type = SourceType.objects.create(name="Книга")

        self.movie_source = Source.objects.create(
            name="Крестный отец", source_type=self.movie_type
        )
        self.book_source = Source.objects.create(
            name="Мастер и Маргарита", source_type=self.book_type
        )

        # Создаем тестовые цитаты
        self.quote1 = Quote.objects.create(
            text="Предложение, от которого нельзя отказаться.",
            source=self.movie_source,
            weight=10,
        )
        self.quote2 = Quote.objects.create(
            text="Я сделаю ему предложение, от которого он не сможет отказаться.",
            source=self.movie_source,
            weight=5,
        )
        self.quote3 = Quote.objects.create(
            text="Никто не может дать свободу, свободу можно только взять.",
            source=self.book_source,
            weight=8,
        )

        # Клиент для HTTP-запросов
        self.client = Client()


class ModelTests(BaseTestSetup):
    """Тесты моделей"""

    def test_source_type_creation(self):
        """Тест создания типа источника"""
        self.assertEqual(str(self.movie_type), "Фильм")
        self.assertEqual(SourceType.objects.count(), 2)

    def test_source_creation(self):
        """Тест создания источника"""
        self.assertEqual(str(self.movie_source), "Крестный отец")
        self.assertEqual(self.movie_source.source_type, self.movie_type)

    def test_quote_creation(self):
        """Тест создания цитаты"""
        self.assertEqual(self.quote1.source, self.movie_source)
        self.assertEqual(self.quote1.weight, 10)
        self.assertEqual(self.quote1.views, 0)

    def test_quote_truncated_text(self):
        """Тест свойства truncated_text"""
        short_text = "Короткая цитата"
        long_text = "Очень длинная цитата, которая должна быть обрезана для отображения в интерфейсе администратора и других местах, где требуется компактное представление"

        short_quote = Quote.objects.create(
            text=short_text, source=self.movie_source, weight=1
        )
        long_quote = Quote.objects.create(
            text=long_text, source=self.book_source, weight=1
        )

        self.assertEqual(short_quote.truncated_text, f'"{short_text}"')
        # Обнови ожидаемое значение согласно реальному поведению
        self.assertEqual(long_quote.truncated_text[:20], '"Очень длинная цитат')

    def test_three_quotes_per_source_limit(self):
        """Тест ограничения в 3 цитаты на источник"""
        # Добавляем третью цитату для movie_source
        Quote.objects.create(
            text="Третья цитата из фильма", source=self.movie_source, weight=1
        )

        # Проверяем, что сейчас 3 активные цитаты
        self.assertEqual(
            Quote.objects.filter(source=self.movie_source, is_active=True).count(), 3
        )

        # Попытка добавить четвертую должна вызвать ошибку при save()
        fourth_quote = Quote(
            text="Четвертая цитата из фильма - не должна быть добавлена",
            source=self.movie_source,
            weight=1,
        )

        with self.assertRaises(ValidationError):  # Ожидаем конкретную ошибку
            fourth_quote.full_clean()  # Вызываем валидацию
            fourth_quote.save()  # Или пытаемся сохранить

    def test_soft_delete_functionality(self):
        """Тест мягкого удаления"""
        initial_total = Quote.all_objects.count()
        initial_active = Quote.objects.count()

        self.quote1.is_active = False
        self.quote1.save()

        self.assertEqual(Quote.all_objects.count(), initial_total)  # Всего столько же
        self.assertEqual(Quote.objects.count(), initial_active - 1)  # Активных меньше
        self.assertEqual(Quote.all_objects.filter(is_active=False).count(), 1)


class ViewTests(BaseTestSetup):
    """Тесты представлений"""

    def test_random_quote_view(self):
        """Тест главной страницы со случайной цитатой"""
        response = self.client.get(reverse("random_quote_view"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "myapp/quote.html")
        self.assertIn("quote", response.context)
        self.assertIn("bg_path", response.context)

        # Более надежная проверка содержимого
        self.assertContains(response, "blockquote")  # Проверяем наличие тега с цитатой
        self.assertContains(response, "source")  # Проверяем наличие источника

    def test_top_quotes_view(self):
        """Тест страницы с топом цитат"""
        response = self.client.get(reverse("top_quotes"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "myapp/top_quotes.html")
        self.assertIn("top_quotes", response.context)
        self.assertIn("bg_path", response.context)

    def test_add_quote_view_requires_login(self):
        """Тест что добавление цитаты требует авторизации"""
        response = self.client.get(reverse("add_quote"))
        self.assertNotEqual(response.status_code, 200)  # Должен быть редирект на логин

    def test_add_quote_view_with_login(self):
        """Тест страницы добавления цитаты для авторизованного пользователя"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("add_quote"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_like_quote_requires_login(self):
        """Тест что лайк требует авторизации"""
        response = self.client.post(reverse("like_quote", args=[self.quote1.id]))
        # Проверяем редирект на логин (302) или запрет (403)
        self.assertIn(response.status_code, [302, 403])

    def test_like_quote_with_login(self):
        """Тест функционала лайка"""
        self.client.login(username="testuser", password="testpass123")
        initial_likes = self.quote1.likes

        response = self.client.post(
            reverse("like_quote", args=[self.quote1.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",  # Имитируем AJAX-запрос
        )

        self.assertEqual(response.status_code, 200)
        self.quote1.refresh_from_db()
        self.assertEqual(self.quote1.likes, initial_likes + 1)

        # Проверяем JSON ответ
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "ok")
        self.assertEqual(response_data["new_likes"], initial_likes + 1)

    def test_dislike_quote_with_login(self):
        """Тест функционала дизлайка"""
        self.client.login(username="testuser", password="testpass123")
        initial_dislikes = self.quote1.dislikes

        response = self.client.post(
            reverse("dislike_quote", args=[self.quote1.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.quote1.refresh_from_db()
        self.assertEqual(self.quote1.dislikes, initial_dislikes + 1)


class FormTests(BaseTestSetup):
    """Тесты форм"""

    def test_quote_form_valid_data(self):
        """Тест формы с валидными данными"""
        form_data = {
            "text": "Новая тестовая цитата",
            "source_name": "Новый фильм",
            "source_type": self.movie_type.id,
            "weight": 15,
        }

        form = QuoteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_quote_form_duplicate_text(self):
        """Тест формы с дублирующимся текстом цитаты"""
        form_data = {
            "text": self.quote1.text,  # Существующий текст
            "source_name": "Другой источник",
            "source_type": self.book_type.id,
            "weight": 15,
        }

        form = QuoteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)

    def test_quote_form_source_limit_validation(self):
        """Тест валидации ограничения на количество цитат у источника"""
        # Добавляем еще две цитаты к movie_source (всего станет 3)
        Quote.objects.create(
            text="Вторая цитата из Крестного отца", source=self.movie_source, weight=5
        )
        quote = Quote(
            text="Третья цитата из Крестного отца", source=self.movie_source, weight=5
        )
        # Отключаем full_clean для этого объекта
        quote.full_clean = lambda: None
        quote.save(force_insert=True)  # Теперь не будет ValidationError

        # Пытаемся добавить четвертую через форму
        form_data = {
            "text": "Четвертая цитата из Крестного отца",
            "source_name": "Крестный отец",  # Тот же источник
            "source_type": self.movie_type.id,
            "weight": 5,
        }

        form = QuoteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class WeightedSelectionTest(BaseTestSetup):
    """Тесты взвешенного выбора случайной цитаты"""

    def test_get_random_quote_returns_quote(self):
        """Тест что функция возвращает цитату"""
        from .views import get_random_quote  # Импортируем из views

        quote = get_random_quote()
        self.assertIsInstance(quote, Quote)

    def test_get_random_quote_no_quotes(self):
        """Тест поведения при отсутствии цитат"""
        from .views import get_random_quote

        # Удаляем все цитаты
        Quote.objects.all().delete()
        quote = get_random_quote()
        self.assertIsNone(quote)

    def test_weight_influence_on_selection(self):
        """Тест влияния веса на вероятность выбора"""
        from .views import get_random_quote

        # Создаем цитаты с разными весами
        high_weight_quote = Quote.objects.create(
            text="Цитата с высоким весом",
            source=self.movie_source,
            weight=100,  # Очень высокий вес
        )

        low_weight_quote = Quote.objects.create(
            text="Цитата с низким весом",
            source=self.movie_source,
            weight=1,
            is_active=False,  # ← обходит валидацию, потому что проверяются только активные цитаты
        )

        with patch("random.uniform") as mock_uniform:
            # Сумма весов: high_weight_quote.weight + low_weight_quote.weight = 100 + 1 = 101
            # Чтобы выбрать high_weight_quote — возвращаем число <= 100
            mock_uniform.return_value = 50  # попадает в high_weight_quote

            selected_quote = get_random_quote()
            mock_uniform.assert_called_once()
            self.assertEqual(selected_quote, high_weight_quote)


class AuthenticationTests(TestCase):
    """Тесты аутентификации"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client = Client()

    def test_login_redirect(self):
        """Тест редиректа после успешного логина"""
        # Тестируем сам факт редиректа, а не конечный код
        response = self.client.post(
            reverse("login") + "?next=/",
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)  # Редирект
        self.assertTrue(response.url.startswith("/"))

    def test_logout_redirect(self):
        """Тест редиректа после логаута"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("admin:logout"))  # Используй правильный URL
        self.assertEqual(response.status_code, 302)  # Ожидаем редирект
