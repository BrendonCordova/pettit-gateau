from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    '''Inline admin interface for viewing purchased items directly within the Order profile.'''
    model = OrderItem
    extra = 0
    readonly_fields = ('price', 'display_subtotal')

    def display_subtotal(self, obj):
        if obj.id:
            return obj.get_subtotal()
        return '-'
    display_subtotal.short_description = 'Subtotal'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    '''Admin interface configuration for managing customer orders and payment statuses.'''
    list_display = ('id', 'customer', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__first_name', 'customer__email', 'id')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('customer', 'address')
        }),
        ('Status e Valores', {
            'fields': ('status', 'total_price')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
