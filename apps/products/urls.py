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
    path('painel/estoque/adicionar-marca/', views.add_brand_quick_view, name='admin-add-brand'),
    path('painel/estoque/adicionar-categoria/', views.add_category_quick_view, name='admin-add-category'),
    path('painel/estoque/editar/<uuid:sku_id>/', views.edit_product_quick_view, name='admin-edit-product'),
    path('painel/estoque/banner/ativar/<uuid:banner_id>/', views.toggle_banner_view, name='admin-toggle-banner'),
    path('painel/estoque/banner/deletar/<uuid:banner_id>/', views.delete_banner_view, name='admin-delete-banner'),
    path('painel/estoque/banner/adicionar/', views.add_banner_inventory_view, name='admin-add-banner-inventory'),
    path('painel/estoque/cupom/adicionar/', views.add_coupon_view, name='admin-add-coupon'),
    path('painel/estoque/cupom/ativar/<uuid:coupon_id>/', views.toggle_coupon_view, name='admin-toggle-coupon'),
]