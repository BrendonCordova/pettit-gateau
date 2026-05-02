from django.urls import path
from .views import CartDetailAPIView

app_name = 'carts_api'

urlpatterns = [
    path('my-cart/', CartDetailAPIView.as_view(), name='cart-detail'),
]