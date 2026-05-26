from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from apps.products.models import SKU
from .serializers import CartSerializer
from django.views.generic import TemplateView

class CartDetailAPIView(APIView):

    def _get_cart(self, request):
        '''Utility (private) method for searching for or creating a shopping cart (DRY)'''
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=session_key)

        return cart

    def get(self, request):

        cart = self._get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request):

        cart = self._get_cart(request)
        sku_id = request.data.get('sku_id')
        quantity = int(request.data.get('quantity', 1))

        if not sku_id:
            return Response({"error": "O ID do SKU (sku_id) é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
    
        sku = get_object_or_404(SKU, id=sku_id)

        existing_item = CartItem.objects.filter(cart=cart, sku=sku).first()
        current_quantity = existing_item.quantity if existing_item else 0

        if current_quantity + quantity > sku.stock_quantity:
            return Response(
                {'error': f'Estoque insuficiente. Temos {sku.stock_quantity} unidades disponíveis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
        else:
            CartItem.objects.get_or_create(
                cart=cart,
                sku=sku,
                quantity=quantity
            )
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        cart = self._get_cart(request)
        sku_id = request.data.get('sku_id')

        if not sku_id:
            return Response({"error": "O ID do SKU (sku_id) é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        item = CartItem.objects.filter(cart=cart, sku_id=sku_id).first()
        if item:
            item.delete()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):

        cart = self._get_cart(request)
        sku_id = request.data.get('sku_id')
        quantity = request.data.get('quantity')

        if not sku_id or quantity is None:
            return Response({"error": "sku_id e quantity são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)
        
        quantity = int(quantity)
        sku = get_object_or_404(SKU, id=sku_id)

        if quantity > sku.stock_quantity:
            return Response(
                {'error': f'Estoque insuficiente. Temos {sku.stock_quantity} unidades disponíveis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            CartItem.objects.filter(cart=cart, sku_id=sku_id).delete()
        else:
            item = CartItem.objects.filter(cart=cart, sku_id=sku_id).first()
            if item:
                item.quantity = quantity
                item.save()
            else:
                return Response({"error": "Item não encontrado no carrinho"}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CartPageView(TemplateView):

    template_name = 'carts/cart_page.html'