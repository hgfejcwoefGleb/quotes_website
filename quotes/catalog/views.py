from .models import Source, SourceType, Quote
from random import choices, choice
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
def get_random_quote()-> Quote:
    """
    Функция отображения для генерации случайной цитаты.
    """
    # Генерация случайной цитаты 
    all_quoetes: list[Quote] = list(Quote.objects.filter(is_active=True))
    weights = [quote.weight for quote in all_quoetes]
    random_quote = choices(all_quoetes, weights=weights)[0]
    random_quote.views += 1
    random_quote.save(update_fields=['views'])
    return random_quote


def random_quote_view(request):
    quote = get_random_quote()
    bg_image = get_random_background_image()
    bg_path = f"myapp/image/{bg_image}"
    return render(request, 'myapp/quote.html', {
        'quote': quote,
        'bg_path': bg_path
    })

def get_random_background_image():
    images_files = ['background1.jpg']
    selected = choice(images_files)
    return f"{selected}"

@csrf_exempt
def like_quote(request, quote_id):
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)
        quote.likes += 1
        quote.save(update_fields=['likes'])  # ← Исправлено: 'likes'
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def dislike_quote(request, quote_id):
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)  # ← Исправлено: Quote вместо quote
        quote.dislikes += 1  # ← Исправлено: dislikes вместо dislike
        quote.save(update_fields=['dislikes'])  # ← Исправлено: update_fields и 'dislikes'
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)