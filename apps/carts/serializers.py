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

    class Meta:
        model = CartItem
        fields = ['id', 'sku', 'product_name', 'volume_ml', 'price', 'quantity', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    '''
    Serializer for the Cart model.
    Nests the associated CartItem objects and includes the dynamically 
    calculated total_price for the entire cart.
    '''
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'session_key', 'items', 'total_price', 'created_at']