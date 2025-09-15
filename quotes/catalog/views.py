from .models import Source, SourceType, Quote
from random import choices, choice
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

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
    if request.user.is_anonymous:
        return JsonResponse({
            'status': 'error', 
            'error': 'auth_required',
            'login_url': f"{settings.LOGIN_URL}?next={request.path}"
        }, status=403)
    
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)
        quote.likes += 1
        quote.save(update_fields=['likes'])
        return JsonResponse({'status': 'ok', 'new_likes': quote.likes})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def dislike_quote(request, quote_id):
    if request.user.is_anonymous:
        return JsonResponse({
            'status': 'error', 
            'error': 'auth_required',
            'login_url': f"{settings.LOGIN_URL}?next={request.path}"
        }, status=403)
    
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)
        quote.dislikes += 1
        quote.save(update_fields=['dislikes'])
        return JsonResponse({'status': 'ok', 'new_dislikes': quote.dislikes})
    return JsonResponse({'status': 'error'}, status=400)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
        try:
            return reverse_lazy('random_quote_view')
        except:
            print("wefwfwf")
            return '/'  # fallback на корень, если что-то пошло не так