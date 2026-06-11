from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import SKU

class CartItemSerializer(serializers.ModelSerializer):
    '''
    Serializer for the CartItem model.
    Flattens related SKU data (name, volume, price) to provide a 
    clean, client-friendly JSON structure.
    '''
    product_name = serializers.CharField(source='sku.product.name', read_only=True)
    volume_ml = serializers.IntegerField(source='sku.volume_ml', read_only=True)
    price = serializers.DecimalField(source='sku.price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'sku', 'product_name', 'volume_ml', 'price', 'quantity', 'subtotal', 'image_url']

    def get_image_url(self, obj):
        '''Retrieves the absolute URL of the product's main image, if available.'''
        main_image = obj.sku.product.images.filter(is_main=True).first()
        if main_image and main_image.image:
            return main_image.image.url
        return None

class CartSerializer(serializers.ModelSerializer):
    '''
    Serializer for the Cart model.
    Nests the associated CartItem objects and includes the dynamically 
    calculated total_price for the entire cart.
    '''
    items = CartItemSerializer(many=True, read_only=True)
    
    subtotal_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True, default=None)

    class Meta:
        model = Cart
        fields = [
            'id', 'session_key', 'items', 'subtotal_price', 
            'cep', 'shipping_name', 'shipping_price', 'shipping_days',
            'coupon_code', 'discount_amount', 'total_price'
        ]