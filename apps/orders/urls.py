from django.urls import path
from .views import checkout_view, order_success_view, mercado_pago_webhook, order_list_view, order_detail_view, order_return_view, confirm_delivery_view

app_name = 'orders'

urlpatterns = [
    path('checkout/', checkout_view, name='checkout'),
    path('sucesso/<uuid:order_id>/', order_success_view, name='success'),
    path('webhook/mercado-pago/', mercado_pago_webhook, name='webhook'),
    path('meus-pedidos/', order_list_view, name='list'),
    path('meus-pedidos/<uuid:pk>/', order_detail_view, name='detail'),
    path('meus-pedidos/<uuid:pk>/devolucao/', order_return_view, name='return'),
    path('meus-pedidos/<uuid:pk>/confirmar-entrega/', confirm_delivery_view, name='confirm-delivery'),
]