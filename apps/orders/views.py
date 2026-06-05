from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.carts.models import Cart
from apps.customers.models import Address
from .models import Order, OrderItem, ShippingMethod, ReturnRequest
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from .services import MercadoPagoService
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import csv

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

                default_shipping = ShippingMethod.objects.filter(is_active=True).first()
                
                frete_price = default_shipping.price if default_shipping else 0
                final_price = cart.total_price + frete_price

                order = Order.objects.create(
                    customer=request.user,
                    address=address,
                    status='PENDING',
                    total_price=final_price,
                    shipping_method=default_shipping
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

                payment_type = payment_data.get('payment_type_id')
                payment_method_id = payment_data.get('payment_method_id')
                installments = payment_data.get('installments', 1)

                format_method = "Mercado Pago"
                if payment_method_id == 'pix':
                    format_method = "Pagamento via PIX"
                elif payment_type == 'credit_card':
                    format_method = f"Cartão de Crédito - {installments}x"
                elif payment_type == 'debit_card':
                    format_method = "Cartão de Débito"
                elif payment_type == 'ticket':
                    format_method = "Boleto Bancário"
                elif payment_type == 'account_money':
                    format_method = "Saldo Mercado Pago"

                if order_id:
                    order = Order.objects.filter(id=order_id).first()

                    if order and status == 'approved' and order.status != 'PAID':
                        order.status = 'PAID'
                        order.payment_approved_at = timezone.now()
                        order.save()

                        order.payment_method = format_method 
                        order.save()

                        for item in order.items.all():
                            item.sku.stock_quantity = F('stock_quantity') - item.quantity
                            item.sku.save()

                        cart = Cart.objects.filter(user=order.customer).first()
                        if cart:
                            cart.items.all().delete()

                        print(f'✅ Pedido {order_id} PAGO via {format_method}!')

            return JsonResponse({'status': 'sucesso'}, status=200)
        
        except Exception as e:
            print(f'Erro no Webhook: {e}')
            return JsonResponse({'error': 'bad_request'}, status=400)
        
    return JsonResponse({'error': 'method_not_allowed'}, status=405)

@login_required(login_url='/conta/login/')
def order_list_view(request):
    '''
    Retrieves and displays a list of the user's orders.
    Supports filtering by product name and order status.
    '''
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')

    search_query = request.GET.get('q')
    status_filter = request.GET.get('status')

    if search_query:
        orders = orders.filter(
            Q(items__sku__product__name__icontains=search_query)
        ).distinct()

    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'current_filters': request.GET,
    }
    return render(request, 'orders/order_list.html', context)

@login_required(login_url='/conta/login/')
def order_detail_view(request, pk):
    '''
    Retrieves and displays the details of a specific order.
    Ensures the user can only view their own orders for security.
    '''
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required(login_url='/conta/login/')
def retry_payment_view(request, pk):
    '''
    Generate a new Mercado Pago payment link for a pending order.
    '''
    order = get_object_or_404(Order, pk=pk, customer=request.user, status='PENDING')
    
    try:
        mp_service = MercadoPagoService()
        preference = mp_service.create_payment_preference(order, order.items.all())
        payment_url = preference['sandbox_init_point']
        return redirect(payment_url)
    except Exception as e:
        messages.error(request, 'Ocorreu um erro ao gerar o novo link de pagamento. Tente novamente mais tarde.')
        return redirect('orders:detail', pk=order.id)

@login_required(login_url='/conta/login/')
def cancel_order_view(request, pk):
    '''
    It allows the customer to cancel an order that is awaiting payment.
    '''
    order = get_object_or_404(Order, pk=pk, customer=request.user, status='PENDING')
    
    if request.method == 'POST':
        order.status = 'CANCELED'
        order.save()
        messages.success(request, 'Seu pedido foi cancelado com sucesso.')
        
    return redirect('orders:detail', pk=order.id)

@login_required(login_url='/conta/login/')
def order_return_view(request, pk):
    '''
    Handles the creation of a product return request.
    Processes selected items, reasons, descriptions, and file uploads.
    - 7 days for 'Arrependimento'
    - 30 days max for defects ('Danificado', 'Produto Incorreto)
    '''
    order = get_object_or_404(Order, pk=pk, customer=request.user)

    if order.status != 'DELIVERED':
        messages.error(request, "Você só pode solicitar a devolução de um pedido que já foi entregue.")
        return redirect('orders:detail', pk=order.id)

    dias_passados = 0
    if order.updated_at:
        dias_passados = (timezone.now() - order.updated_at).days

    if dias_passados > 30:
        messages.error(request, "O prazo legal máximo de 30 dias para devoluções ou reclamações expirou.")
        return redirect('orders:detail', pk=order.id)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        if reason == 'Arrependimento' and dias_passados > 7:
            messages.error(request, "O prazo de 7 dias para devolução por arrependimento expirou. Selecione outro motivo se o produto apresentar defeito.")
            return redirect('orders:return', pk=order.id)

        items_ids = request.POST.getlist('return_items')
        action = request.POST.get('action')
        description = request.POST.get('description')
        media = request.FILES.get('media')

        if not items_ids:
            messages.error(request, "Selecione pelo menos um produto para devolver.")
            return redirect('orders:return', pk=order.id)

        return_req = ReturnRequest.objects.create(
            order=order,
            reason=reason,
            action=action,
            description=description,
            media=media
        )
        
        for item_id in items_ids:
            return_req.items.add(item_id)

        assunto = f"Solicitação de Devolução Recebida - Pettit Gateau"
        mensagem = f"""Olá, {order.customer.first_name}!

Recebemos a sua solicitação de devolução referente ao pedido #{str(order.id)[:8]}.
O número da sua solicitação é: #{return_req.id}

Nossa equipe analisará sua solicitação em até 3 dias úteis.
Você receberá atualizações pelo seu e-mail cadastrado.

Atenciosamente,
Equipe Pettit Gateau"""
        
        try:
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [order.customer.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erro ao enviar e-mail de devolução: {e}")

        return redirect('orders:return-success', return_id=return_req.id)

    return render(request, 'orders/order_return.html', {'order': order})

@login_required(login_url='/conta/login/')
def order_return_success_view(request, return_id):
    '''
    Exibe a página de sucesso após uma solicitação de devolução.
    '''
    return_req = get_object_or_404(ReturnRequest, id=return_id, order__customer=request.user)
    return render(request, 'orders/order_return_success.html', {'return_req': return_req})

@login_required(login_url='/conta/login/')
def confirm_delivery_view(request, pk):
    '''
    Permite ao cliente confirmar manualmente que recebeu o produto.
    Muda o status para DELIVERED e atualiza a data (updated_at) para iniciar o prazo de devolução.
    '''
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    
    if order.status == 'SHIPPED':
        order.status = 'DELIVERED'
        order.save()
        messages.success(request, "Entrega confirmada! Esperamos que adore a sua nova fragrância.")
        
    return redirect('orders:detail', pk=order.id)

@staff_member_required(login_url='/conta/login/')
def admin_orders_dashboard_view(request):
    orders = Order.objects.all().order_by('-created_at')

    agregado = orders.filter(
        status__in=['PAID', 'PREPARING', 'SHIPPED', 'DELIVERED']
    ).aggregate(total=Sum('total_price'))
    
    total_revenue = agregado['total'] if agregado['total'] is not None else 0.00

    status_counts = {
        'a_caminho': orders.filter(status='SHIPPED').count(),
        'a_enviar': orders.filter(status__in=['PAID', 'PREPARING']).count(),
        'aguardando': orders.filter(status='PENDING').count(),
        'cancelado': orders.filter(status='CANCELED').count(),
    }

    context = {
        'orders': orders,
        'total_revenue': total_revenue,
        'status_counts': status_counts,
        'total_pedidos': orders.count(),
    }
    return render(request, 'orders/admin_dashboard.html', context)

@staff_member_required(login_url='/conta/login/')
def update_order_status_view(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
        
        messages.success(request, f"Status do pedido #{str(order.id)[:8]} atualizado com sucesso!")
        
    return redirect('orders:admin-dashboard')

@staff_member_required(login_url='/conta/login/')
def export_data_view(request, export_type):
    response = HttpResponse(content_type='text/csv')
    nome_arquivo = f"relatorio_{export_type}_{timezone.now().strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')

    if export_type == 'faturamento':
        writer.writerow(['ID do Pedido', 'Data da Compra', 'Cliente', 'Status', 'Método de Pagamento', 'Total (R$)'])
        orders = Order.objects.all().select_related('customer')
        for order in orders:
            preco_br = str(order.total_price).replace('.', ',')
            writer.writerow([order.id, order.created_at.strftime("%d/%m/%Y %H:%M"), order.customer.first_name, order.get_status_display(), order.payment_method, preco_br])

    elif export_type == 'clientes':
        writer.writerow(['Nome', 'E-mail', 'Qtd de Pedidos Feitos'])
        from apps.customers.models import Customer
        customers = Customer.objects.all()
        for c in customers:
            writer.writerow([c.first_name, c.email, c.orders.count()])

    elif export_type == 'todos_os_dados':
        writer.writerow(['ID do Pedido', 'Data', 'Cliente', 'Produto', 'Volume (ml)', 'Quantidade', 'Preço Unitário na Compra (R$)'])
        items = OrderItem.objects.all().select_related('order', 'sku__product', 'order__customer')
        for item in items:
            preco_br = str(item.price).replace('.', ',')
            writer.writerow([item.order.id, item.order.created_at.strftime("%d/%m/%Y"), item.order.customer.first_name, item.sku.product.name, item.sku.volume_ml, item.quantity, preco_br])

    return response