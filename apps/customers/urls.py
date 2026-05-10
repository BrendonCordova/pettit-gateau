from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomerLoginView, register_view, address_create_view

app_name = 'customers'

urlpatterns = [
    path('login/', CustomerLoginView.as_view(), name='login'),
    path('cadastro/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('endereco/novo/', address_create_view, name='adress-create'),
]