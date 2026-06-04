from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('vitrine/', views.product_list, name='list'),
    path('categoria/<str:category_name>/', views.product_list, name='category_list'),
    path('<slug:slug>/', views.product_detail, name='detail'),
    path('<slug:slug>/avaliacoes/api/', views.load_more_reviews_api, name='api_reviews'),
    path('painel/estoque/', views.admin_inventory_view, name='admin-inventory'),
    path('painel/estoque/adicionar/', views.add_product_quick_view, name='admin-add-product'),
]