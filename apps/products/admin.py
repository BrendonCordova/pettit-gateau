from django.contrib import admin
from .models import Brand, Category, Product, SKU, ProductImage, Review, Banner

admin.site.register(Brand)
admin.site.register(Category)

class ProductImageInline(admin.TabularInline):
    '''Inline admin interface for managing product images directly from the Product view.'''
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    '''Admin interface configuration for the Product model.'''
    list_display = ('name', 'brand', 'category', 'is_active')
    list_filter = ('brand', 'category', 'is_active')
    search_fields = ('name',)
    inlines = [ProductImageInline]

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    '''Admin interface configuration for the SKU model.'''
    list_display = ('sku_code', 'product', 'concentration', 'volume_ml', 'price', 'stock_quantity')
    search_fields = ('sku_code', 'product__name')
    list_filter = ('concentration', 'volume_ml')
    list_editable = ('price', 'stock_quantity')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    '''Admin interface configuration for the Review model.'''
    list_display = ('product', 'customer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer__first_name', 'product__name')

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    '''Admin interface configuration for the Banner promotional model.'''
    list_display = ('title', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title',)
