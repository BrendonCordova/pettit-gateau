from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('<slug:slug>/', views.product_detail, name='detail'),
    path('<slug:slug>/avaliacoes/api/', views.load_more_reviews_api, name='api_reviews'),
]