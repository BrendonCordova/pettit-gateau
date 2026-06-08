from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from apps.products.models import SKU
from .serializers import CartSerializer
from django.views.generic import TemplateView
from django.contrib import messages
from .models import Coupon
from .serializers import CartSerializer
from .services import CorreiosService
from decimal import Decimal

class CartDetailAPIView(APIView):
    '''
    API endpoint for managing the shopping cart.
    Handles retrieving, adding, updating, and removing items from a user's cart.
    Supports both authenticated users and anonymous sessions.
    '''
    def _get_cart(self, request):
        '''
        Utility method to retrieve or create a shopping cart.
        Links the cart to the authenticated user or to the anonymous session key.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            Cart: The active shopping cart instance for the current user/session.
        '''
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=session_key)

        return cart

    def get(self, request):
        '''
        Retrieves the current state of the shopping cart.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            Response: A serialized JSON response containing cart details and total price.
        '''
        cart = self._get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request):
        '''
        Adds a new item to the shopping cart or increments its quantity.
        Validates available stock before confirming the addition.

        Args:
            request (HttpRequest): The HTTP request containing 'sku_id' and 'quantity'.

        Returns:
            Response: A JSON response with the updated cart data (HTTP 200) 
                      or an error message if stock is insufficient (HTTP 400).
        '''
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
            messages.success(request, f"A quantidade de {sku.product.name} foi atualizada no seu carrinho!")
        else:
            CartItem.objects.get_or_create(
                cart=cart,
                sku=sku,
                quantity=quantity
            )
            messages.success(request, f"🐾 {sku.product.name} foi adicionado ao seu carrinho com sucesso!")
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        '''
        Removes a specific SKU entirely from the shopping cart.

        Args:
            request (HttpRequest): The HTTP request containing the 'sku_id' to remove.

        Returns:
            Response: A JSON response with the updated cart data.
        '''
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
        '''
        Updates the exact quantity of an existing item in the shopping cart.
        Removes the item if the quantity is updated to 0 or less.

        Args:
            request (HttpRequest): The HTTP request containing 'sku_id' and the new 'quantity'.

        Returns:
            Response: A JSON response with the updated cart data or a stock error.
        '''
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
    '''
    Class-based view to render the frontend shopping cart interface.
    The actual data population is handled asynchronously via the CartDetailAPIView.
    '''
    template_name = 'carts/cart_page.html'

class CartShippingAPIView(APIView):
    def post(self, request):
        '''
        Receives the zip code, checks with the postal service, and returns the options.
        If the customer submits their final choice, it is saved to the cart.
        '''
        cart = CartDetailAPIView()._get_cart(request)
        cep = request.data.get('cep')
        
        if cep and not request.data.get('shipping_name'):
            correios = CorreiosService()
            peso_total = max(cart.items.count() * 0.5, 1) 
            resposta = correios.calcular_frete(cep_destino=cep, peso=peso_total)
            
            if isinstance(resposta, dict) and 'error' in resposta:
                return Response(resposta, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({'opcoes': resposta})

        shipping_name = request.data.get('shipping_name')
        shipping_price = request.data.get('shipping_price')
        shipping_days = request.data.get('shipping_days')

        if shipping_name and shipping_price:
            cart.cep = cep
            cart.shipping_name = shipping_name
            cart.shipping_price = Decimal(str(shipping_price))
            cart.shipping_days = int(shipping_days)
            cart.save()
            return Response(CartSerializer(cart).data)
            
        return Response({"error": "Dados inválidos."}, status=status.HTTP_400_BAD_REQUEST)

class CartCouponAPIView(APIView):
    def post(self, request):
        cart = CartDetailAPIView()._get_cart(request)
        code = request.data.get('code')
        
        if not code:
            cart.coupon = None
            cart.save()
            return Response(CartSerializer(cart).data)

        coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
        if not coupon:
            return Response({"error": "Cupom inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)
        
        cart.coupon = coupon
        cart.save()
        return Response(CartSerializer(cart).data)