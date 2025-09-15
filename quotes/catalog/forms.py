from django import forms

from .models import Quote, Source, SourceType


class QuoteForm(forms.ModelForm):
    source_name = forms.CharField(
        max_length=500,
        label="Название источника",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Например: Альберт Эйнштейн, Мастер и Маргарита...",
            }
        ),
    )
    source_type = forms.ModelChoiceField(
        queryset=SourceType.objects.all(),
        label="Тип источника",
        empty_label="Выберите тип источника",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Quote
        fields = ["text", "weight"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "placeholder": "Введите текст цитаты...",
                }
            ),
            "weight": forms.NumberInput(
                attrs={"class": "form-input", "min": 1, "max": 100}
            ),
        }

    def clean_text(self):
        text = self.cleaned_data.get("text")
        if text and Quote.objects.filter(text__iexact=text).exists():
            raise forms.ValidationError("Цитата с таким текстом уже существует.")
        return text

    def clean(self):
        cleaned_data = super().clean()
        source_name = cleaned_data.get("source_name")
        source_type = cleaned_data.get("source_type")

        if source_name and source_type:
            existing_quotes = Quote.objects.filter(
                source__name__iexact=source_name,
                source__source_type=source_type,
                is_active=True,
            ).count()

            if existing_quotes >= 3:
                raise forms.ValidationError(
                    f"У источника '{source_name}' (тип: {source_type}) уже есть 3 активные цитаты. Нельзя добавить больше."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        source_name = self.cleaned_data["source_name"]
        source_type = self.cleaned_data["source_type"]

        source, created = Source.objects.get_or_create(
            name__iexact=source_name,
            source_type=source_type,
            defaults={"name": source_name, "source_type": source_type},
        )

        instance.source = source

        if commit:
            try:
                instance.save()
            except forms.ValidationError as e:
                self.add_error(None, str(e))
                raise

        return instance
