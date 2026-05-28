from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.carts.models import Cart
from apps.customers.models import Address
from .models import Order, OrderItem
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from .services import MercadoPagoService
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='/conta/login/')
def checkout_view(request):
    '''
    Handles the checkout process for authenticated users.
    Validates cart availability and stock levels, creates the order and order items 
    within a database transaction, and generates a Mercado Pago payment preference.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A redirection to the Mercado Pago sandbox checkout URL, 
                      or the rendered 'checkout.html' template displaying validation errors.
        
    Raises:
        ValueError: If a cart item's requested quantity exceeds available stock.
    '''
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or cart.items.count() == 0:
        return redirect('products:list')
    
    address = Address.objects.filter(customer=request.user, is_default=True).first() or \
        Address.objects.filter(customer=request.user).first()

    if not address:

        messages.info(request, 'Para finalizar sua compra, precisamos que você cadastre um endereço de entrega.')
        return redirect('customers:address-create')

    if request.method == 'POST':

        try:
            with transaction.atomic():

                for cart_item in cart.items.all():
                    if cart_item.sku.stock_quantity < cart_item.quantity:
                        raise ValueError(f'Desculpe, o produto {cart_item.sku.product.name} não tem estoque suficiente.')

                order = Order.objects.create(
                    customer=request.user,
                    address=address,
                    status='PENDING',
                    total_price=cart.total_price
                )

                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        sku=cart_item.sku,
                        price=cart_item.sku.price,
                        quantity=cart_item.quantity
                    )

                mp_service = MercadoPagoService()

                preference = mp_service.create_payment_preference(order, cart.items.all())

                payment_url = preference['sandbox_init_point']

            return redirect(payment_url)
       
        except ValueError as e:
            return render(request, 'orders/checkout.html', {'cart': cart, 'address': address, 'error': str(e)})
        except Exception as e:
            print("ERRO FATAL:", e)
            return render(request, 'orders/checkout.html', {'cart': cart, 'address': address, 'error': 'Ocorreu um erro ao comunicar com o banco. Tente novamente.'})

    context = {
        'cart': cart,
        'address': address
    }
    return render(request, 'orders/checkout.html', context)

@login_required(login_url='/conta/login/')
def order_success_view(request, order_id):
    '''
    Renders the success page after a user returns from the payment gateway.
    Clears the active shopping cart upon successful order placement.

    Args:
        request (HttpRequest): The HTTP request object.
        order_id (uuid): The unique identifier of the placed order.

    Returns:
        HttpResponse: The rendered 'success.html' template containing order details.
    '''
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    cart = Cart.filter(user=request.user).first()
    if cart:
        cart.items.all().delete()

    return render(request, 'orders/success.html', {'order': order})

@csrf_exempt
def mercado_pago_webhook(request):
    '''
    Asynchronous webhook endpoint for receiving payment status updates from Mercado Pago.
    If a payment is approved, it updates the order status to 'PAID', safely deducts 
    the purchased quantities from the inventory, and clears the user's cart.

    Args:
        request (HttpRequest): The HTTP POST request containing the JSON payload from Mercado Pago.

    Returns:
        JsonResponse: A JSON response with HTTP 200 on success, 400 on parsing errors, 
                      or 405 for disallowed HTTP methods.
    '''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            resource_id = data.get('data', {}).get('id') or data.get('resource')
            topic = data.get('type') or data.get('topic')

            if topic == 'payment' and resource_id:
                mp_service = MercadoPagoService()

                payment_info = mp_service.sdk.payment().get(resource_id)
                payment_data = payment_info['response']

                status = payment_data.get('status')
                order_id = payment_data.get('external_reference')

                if order_id:
                    order = Order.objects.filter(id=order_id).first()

                    if order and status == 'approved' and order.status != 'PAID':
                        order.status = 'PAID'
                        order.save()

                        for item in order.items.all():
                            item.sku.stock_quantity = F('stock_quantity') - item.quantity
                            item.sku.save()

                        cart = Cart.objects.filter(user=order.customer).first()
                        if cart:
                            cart.items.all().delete()

                        print(f'✅ Pedido {order_id} atualizado para PAGO via webhook!')

            return JsonResponse({'status': 'sucesso'}, status=200)
        
        except Exception as e:
            print(f'Erro no Webhook: {e}')
            return JsonResponse({'error': 'bad_request'}, status=400)
        
    return JsonResponse({'error': 'method_not_allowed'}, status=405)