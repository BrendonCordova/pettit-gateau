from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomerLoginView, register_view, address_create_view, verify_email_view, profile_view, profile_update_view, address_update_view

app_name = 'customers'

urlpatterns = [
    path('login/', CustomerLoginView.as_view(), name='login'),
    path('cadastro/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('endereco/novo/', address_create_view, name='address-create'),
    path('endereco/<uuid:pk>/editar/', address_update_view, name='address-update'),
    path('ativar/<uidb64>/<token>/', verify_email_view, name='verify-email'),
    path('perfil/', profile_view, name='profile'),
    path('perfil/editar/', profile_update_view, name='profile-update'),
]