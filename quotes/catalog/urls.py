from django.urls import path
from . import views


urlpatterns = [
    path('', views.random_quote_view, name='random_quote_view'),
    path('like/<uuid:quote_id>/', views.like_quote, name='like_quote'),
    path('dislike/<uuid:quote_id>/', views.dislike_quote, name='dislike_quote'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'), 
    path('add-quote/', views.add_quote, name='add_quote'),
    path('top/', views.top_quotes_view, name='top_quotes'),
]

