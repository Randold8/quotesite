from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('', views.random_quote_view, name='random'),
    path('add/', views.add_quote_view, name='add_quote'),
    path('source/add/', views.add_source_view, name='add_source'),
    path('top/', views.top_quotes_view, name='top'),
    path('vote/<int:pk>/<str:action>/', views.vote_quote_view, name='vote'),
]