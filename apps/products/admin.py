from django.contrib import admin
from .models import Brand, Category, Product, SKU

admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Product)

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'product', 'concentration', 'volume_ml', 'price', 'stock_quantity')
    search_fields = ('sku_code', 'product__name')
    list_filter = ('concentration', 'volume_ml')
    list_editable = ('price', 'stock_quantity')
