from django.urls import path
from .views import CustomerLoginView, register_view, address_create_view, verify_email_view, profile_view, profile_update_view, address_update_view, logout_view

app_name = 'customers'

urlpatterns = [
    path('login/', CustomerLoginView.as_view(), name='login'),
    path('cadastro/', register_view, name='register'),
    path('endereco/novo/', address_create_view, name='address-create'),
    path('endereco/<uuid:pk>/editar/', address_update_view, name='address-update'),
    path('ativar/<uidb64>/<token>/', verify_email_view, name='verify-email'),
    path('perfil/', profile_view, name='profile'),
    path('perfil/editar/', profile_update_view, name='profile-update'),
    path('logout/', logout_view, name='logout'),
]