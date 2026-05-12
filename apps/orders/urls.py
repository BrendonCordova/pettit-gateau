from django.urls import path
from .views import checkout_view, order_success_view, mercado_pago_webhook

app_name = 'orders'

urlpatterns = [
    path('checkout/', checkout_view, name='checkout'),
    path('sucesso/<uuid:order_id>/', order_success_view, name='success'),
    path('webhook/mercado-pago/', mercado_pago_webhook, name='webhook'),
]