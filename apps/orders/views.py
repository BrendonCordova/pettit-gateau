from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.carts.models import Cart
from apps.customers.models import Address
from .models import Order, OrderItem
from django.db import transaction
from django.db.models import F
from django.contrib import messages

@login_required(login_url='/conta/login/')
def checkout_view(request):

    cart = Cart.objects.filter(user=request.user).first()

    if not cart or cart.items.count() == 0:
        return redirect('products:list')
    
    address = Address.objects.filter(customer=request.user, is_default=True).first() or \
        Address.objects.filter(customer=request.user).first()

    if not address:
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

                    cart_item.sku.stock_quantity = F('stock_quantity') - cart_item.quantity
                    cart_item.sku.save()
                    cart_item.sku.refresh_from_db()

                cart.items.all().delete()

            return redirect('orders:success', order_id=order.id)
       
        except ValueError as e:

            return render(request, 'orders/checkout.html', {'cart': cart, 'address': address, 'error': str(e)})
    
    context = {
        'cart': cart,
        'address': address
    }
    return render(request, 'orders/checkout.html', context)

@login_required(login_url='/conta/login/')
def order_success_view(request, order_id):

    order = get_object_or_404(Order, id=order_id, customer=request.user)

    return render(request, 'orders/success.html', {'order': order})