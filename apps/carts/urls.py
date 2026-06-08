from django.urls import path
from .views import CartDetailAPIView, CartPageView, CartShippingAPIView, CartCouponAPIView

app_name = 'carts'

urlpatterns = [
    path('', CartPageView.as_view(), name='cart-page'),
    path('api/my-cart/', CartDetailAPIView.as_view(), name='cart-api'),
    path('api/my-cart/shipping/', CartShippingAPIView.as_view(), name='cart-shipping'),
    path('api/my-cart/coupon/', CartCouponAPIView.as_view(), name='cart-coupon'),
]