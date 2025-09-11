from django.contrib import admin
from .models import SourceType, Quote, Source
from django import forms

READONLY_FIELDS = ['id', 'is_active', 'created_at', 'updated_at']

admin.site.register(SourceType)
@admin.register(Source)
class Source(admin.ModelAdmin):
    list_display = ('name', 'source_type')

class QuoteAdminForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            for field in READONLY_FIELDS.extend(['views', 'likes', 'dislikes']):
                self.fields[field].widget = forms.HiddenInput()



@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    
    list_display = ("__str__", 'source', 'weight', 'views', 'likes', 'dislikes')
    list_filter = ('weight', 'views', 'likes', 'dislikes')
    list_editable = ('weight', )
    readonly_fields = READONLY_FIELDS

    add_fieldsets = [
        (None, {
            'fields': ['text', 'source', 'weight'],
            'description': 'Заполните основные поля цитаты'
        })
    ]
    
    fieldsets = [
        (None, {
            'fields': ['text', 'source'],
            'description': 'Основная информация о цитате'
        }),
        ('Статистика', {
            'fields': ['views', 'likes', 'dislikes'],
            'classes': ['collapse'],
            'description': 'Статистика просмотров и реакций'
        }),
        ('Настройки', {
            'fields': ['weight'],
            'description': 'Настройки отображения цитаты'
        }),
        ('Системная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
            'description': 'Автоматически заполняемые поля'
        })
    ]

    def get_readonly_fields(self, request, obj = ...):
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser: # or obj: следует добавить сюда, т.к. данная информация должная быть недоступна всем после создания 
            readonly_fields.extend(['views', 'likes', 'dislikes'])
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # только при создании
            active_quotes_count = Quote.objects.filter(source=obj.source, is_active=True).count()
            if active_quotes_count >= 3:
                from django.contrib import messages
                self.message_user(
                    request, 
                    f"Нельзя добавить цитату. У источника '{obj.source}' уже есть 3 активные цитаты.", 
                    level=messages.ERROR
                )
                return  # не сохраняем объект
        
        super().save_model(request, obj, form, change)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return self.fieldsets

