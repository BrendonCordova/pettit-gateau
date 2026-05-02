from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from apps.products.models import SKU
from .serializers import CartSerializer

class CartDetailAPIView(APIView):

    def get(self, request):

        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=session_key)

        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request):

        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            cart, _ = Cart.objects.get_or_create(session_key=session_key)

        sku_id = request.data.get('sku_id')
        quantity = int(request.data.get('quantity', 1))

        if not sku_id:
            return Response({"error": "O ID do SKU (sku_id) é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
    
        sku = get_object_or_404(SKU, id=sku_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            sku=sku,
            defaults={'quantity':quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)