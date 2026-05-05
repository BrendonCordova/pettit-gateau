from django.urls import path
from .views import CartDetailAPIView, CartPageView

app_name = 'carts'

urlpatterns = [
    path('', CartPageView.as_view(), name='cart-page'),

    path('api/my-cart/', CartDetailAPIView.as_view(), name='cart-api'),
]