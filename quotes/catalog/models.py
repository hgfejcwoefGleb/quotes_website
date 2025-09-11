from tabnanny import check, verbose
from turtle import mode
from django import views
from django.db import models
import uuid
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from networkx import constraint

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
    
    def active(self):
        return self.get_queryset().active()
    
    def inactive(self):
        return self.get_queryset().inactive()
    
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None
    
    def create_if_not_exists(self, defaults=None, **kwargs):
        """Создает объект, если он не существует"""
        obj, created = self.get_or_create(defaults=defaults, **kwargs)
        return obj, created
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    
     # Кастомный менеджер

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    objects = BaseManager() 

    class Meta:
        abstract = True
        ordering = ['-created_at']

class Source(BaseModel):
    name = models.TextField(verbose_name="Название источника")
    source_type = models.CharField(max_length=255, verbose_name="Вид источника: фильм, книга и тп")
    author = models.CharField(max_length=255, verbose_name="Автор источника")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"
        ordering = ["-created_at"]
        unique_together = ["name", "author"]

class Quote(BaseModel):
    text = models.TextField(verbose_name="Цитата", unique=True)
    source = models.ForeignKey('Source', on_delete=models.CASCADE, verbose_name="Источник")
    weight = models.PositiveIntegerField(verbose_name="Вес")
    weight = models.PositiveIntegerField(default=1, verbose_name="Вес (влияет на частоту показа)")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    likes = models.IntegerField(default=0, verbose_name="Лайки")
    dislikes = models.IntegerField(default=0, verbose_name="Дизлайки")

    def __str__(self):
        return f'"{self.text[:50]}..." из {self.source.name}'
    
    class Meta:
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(likes__gte=0),
                name="likes_gte0" 
            ),
            models.CheckConstraint(
                check=models.Q(dislikes_gte=0),
                name="dislikes_gte0"
            ),
            models.CheckConstraint(
                check=models.Q(views_gte=0),
                name="views_gte0"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk:  # только при создании
            active_quotes_count = Quote.objects.filter(source=self.source, is_active=True).count()
            if active_quotes_count >= 3:
                raise ValidationError(f"У источника '{self.source}' уже есть 3 активные цитаты. Нельзя добавить больше.")
        super().save(*args, **kwargs)