from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    '''Inline admin interface for viewing cart items directly inside a Cart record.'''
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['sku', 'quantity', 'subtotal']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    '''Admin interface configuration for the Cart model.'''
    list_display = ['id', 'user', 'session_key', 'created_at']
    list_filter = ['created_at']
    inlines = [CartItemInline]
    readonly_fields = ['display_total']

    def display_total(self, obj):
        return f'R$ {obj.total_price}'
    display_total.short_description = 'Total do Carrinho'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    '''Admin interface configuration for the CartItem model.'''
    list_display = ['id', 'cart', 'sku', 'quantity']