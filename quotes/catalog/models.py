import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet


class SoftDeleteQuerySet(QuerySet):
    """Кастомный QuerySet для мягкого удаления"""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def delete(self):
        return self.update(is_active=False)

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return self.update(is_active=True)


class BaseManager(models.Manager):
    """Базовый менеджер с полезными методами"""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
    """Базовая модель, от которой будут наследоваться остальные"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    all_objects = models.Manager()
    objects = BaseManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save(update_fields=["is_active"])


class SourceType(BaseModel):
    name = models.CharField(
        max_length=255, verbose_name="Вид источника: фильм, книга и тп", unique=True
    )

    class Meta:
        verbose_name = "Вид источника"
        verbose_name_plural = "Виды источников"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Source(BaseModel):
    """Модель источника цитаты"""

    name = models.TextField(verbose_name="Название источника")
    source_type = models.ForeignKey(
        max_length=255,
        verbose_name="Вид источника: фильм, книга и тп",
        to="SourceType",
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"
        ordering = ["-created_at"]
        unique_together = ["name", "source_type"]

    def __str__(self):
        return self.name


class Quote(BaseModel):
    """Модель цитаты"""

    text = models.TextField(verbose_name="Цитата", unique=True)
    source = models.ForeignKey(
        "Source", on_delete=models.CASCADE, verbose_name="Источник"
    )
    weight = models.PositiveIntegerField(
        default=1, verbose_name="Вес (влияет на частоту показа)"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    likes = models.IntegerField(default=0, verbose_name="Лайки")
    dislikes = models.IntegerField(default=0, verbose_name="Дизлайки")

    @property
    def truncated_text(self):
        """Свойство для получения сокращенного текста"""
        if len(self.text) > 50:
            return f'"{self.text[:47]}..."'
        return f'"{self.text}"'

    def __str__(self):
        return self.truncated_text

    class Meta:
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(check=models.Q(likes__gte=0), name="likes_gte0"),
            models.CheckConstraint(
                check=models.Q(dislikes__gte=0), name="dislikes_gte0"
            ),
            models.CheckConstraint(check=models.Q(views__gte=0), name="views_gte0"),
        ]

    def clean(self):
        if hasattr(self, "source") and self.source and self.is_active:
            existing_quotes = Quote.objects.filter(source=self.source, is_active=True)
            if self.pk:
                existing_quotes = existing_quotes.exclude(pk=self.pk)
            if existing_quotes.count() >= 3:
                raise ValidationError(
                    f"У источника '{self.source}' уже есть 3 активные цитаты."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
