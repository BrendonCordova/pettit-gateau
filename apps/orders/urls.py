from django.urls import path
from .views import checkout_view, order_success_view, mercado_pago_webhook, order_list_view

app_name = 'orders'

urlpatterns = [
    path('checkout/', checkout_view, name='checkout'),
    path('sucesso/<uuid:order_id>/', order_success_view, name='success'),
    path('webhook/mercado-pago/', mercado_pago_webhook, name='webhook'),
    path('meus-pedidos/', order_list_view, name='list'),
]