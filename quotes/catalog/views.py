import random
from random import choice

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.forms import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .forms import QuoteForm
from .models import Quote


def get_random_quote():
    total_weight = Quote.objects.aggregate(total=Sum("weight"))["total"]
    if not total_weight:
        return None
    random_weight = random.uniform(0, total_weight)
    current = 0
    for quote in (
        Quote.objects.all().filter(is_active=True).only("id", "weight").order_by("id")
    ):
        current += quote.weight
        if current >= random_weight:
            return Quote.objects.get(pk=quote.pk)


def random_quote_view(request):
    quote = get_random_quote()
    if quote:
        quote.views += 1  # Предполагается, что в модели Quote есть поле views
        quote.save(update_fields=["views"])
    bg_image = get_random_background_image()
    bg_path = f"myapp/image/{bg_image}"
    form = QuoteForm()
    return render(
        request, "myapp/quote.html", {"quote": quote, "bg_path": bg_path, "form": form}
    )


def get_random_background_image():
    images_files = [
        "background1.jpg",
        "background2.jpg",
        "background3.jpg",
        "background4.jpg",
    ]
    selected = choice(images_files)
    return f"{selected}"


@login_required
@require_POST
def like_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    quote.likes += 1
    quote.save(update_fields=["likes"])
    return JsonResponse({"status": "ok", "new_likes": quote.likes})


@login_required
@require_POST
def dislike_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    quote.dislikes += 1
    quote.save(update_fields=["dislikes"])
    return JsonResponse({"status": "ok", "new_dislikes": quote.dislikes})


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        try:
            return reverse_lazy("random_quote_view")
        except:
            print("wefwfwf")
            return "/"


@login_required
def add_quote(request):
    if request.method == "POST":
        form = QuoteForm(request.POST)
        if form.is_valid():
            try:
                quote = form.save(commit=False)
                quote.save()
                messages.success(request, "Цитата успешно добавлена!")
                return redirect("random_quote_view")
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Ошибка при сохранении: {str(e)}")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = QuoteForm()

    quote = get_random_quote()
    bg_path = f"myapp/image/{get_random_background_image()}"

    return render(
        request, "myapp/quote.html", {"quote": quote, "bg_path": bg_path, "form": form}
    )


def top_quotes_view(request):
    top_quotes = Quote.objects.filter(is_active=True).order_by("-likes")[:20]
    bg_path = f"myapp/image/{get_random_background_image()}"
    return render(
        request, "myapp/top_quotes.html", {"top_quotes": top_quotes, "bg_path": bg_path}
    )
