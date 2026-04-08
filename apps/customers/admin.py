from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'tax_id')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)

    fieldsets = (
        ('Credenciais de Acesso', {
            'fields': ('email', 'password')
        }),
        ('Informações Pessoais', {
            'fields': ('first_name', 'last_name', 'tax_id', 'birth_date', 'phone')
        }),
        ('Permissões e Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
    )