from django.contrib import admin
from .models import Brand, Category, Product, SKU, ProductImage

admin.site.register(Brand)
admin.site.register(Category)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'is_active')
    list_filter = ('brand', 'category', 'is_active')
    search_fields = ('name',)
    inlines = [ProductImageInline]

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'product', 'concentration', 'volume_ml', 'price', 'stock_quantity')
    search_fields = ('sku_code', 'product__name')
    list_filter = ('concentration', 'volume_ml')
    list_editable = ('price', 'stock_quantity')
