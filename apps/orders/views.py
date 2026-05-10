from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.carts.models import Cart
from apps.customers.models import Address
from .models import Order, OrderItem

@login_required(login_url='/conta/login/')
def checkout_view(request):

    cart = Cart.objects.filter(user=request.user).first()

    if not cart or cart.items.count() == 0:
        return redirect('products:list')
    
    address = Address.objects.filter(customer=request.user, is_default=True).first()

    if not address:
        address = Address.objects.filter(customer=request.user).first()

    if not address:
        return redirect('customers:address-create')

    if request.method == 'POST':

        if not address:
            # The address form still needs to be implemented
            return render(request, 'orders/checkout.html', {'cart': cart, 'error': 'Você precisa de um endereço cadastrado.'})

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

        cart.items.all().delete()

        return redirect('orders:success', order_id=order.id)
    
    context = {
        'cart': cart,
        'address': address
    }
    return render(request, 'orders/checkout.html', context)

@login_required(login_url='/conta/login/')
def order_success_view(request, order_id):

    order = get_object_or_404(Order, id=order_id, customer=request.user)

    return render(request, 'orders/success.html', {'order': order})