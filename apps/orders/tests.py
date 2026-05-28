from django.test import TestCase
from django.urls import reverse
from apps.customers.models import Customer, Address
from apps.products.models import Product, Brand, Category, SKU
from apps.carts.models import Cart, CartItem
from .models import Order
from unittest.mock import patch
import json

class OrderCreationTestCase(TestCase):
    '''
    Test suite for the order creation flow.
    Verifies the conversion of a shopping cart into a pending order 
    and the correct handling of database transactions.
    '''
    def setUp(self):
        '''
        Sets up the required database state, including mock customers, addresses, 
        products, SKUs, and a populated shopping cart.
        '''
        self.customer = Customer.objects.create(first_name='João', last_name='Teste', email='joao@teste.com')
        self.client.force_login(self.customer)

        self.address = Address.objects.create(
            customer=self.customer, 
            street='Rua Teste', 
            number='123', 
            city='Laguna', 
            state='SC', 
            zip_code='88790-000'
        )

        self.brand = Brand.objects.create(name='Marca Teste')
        self.category = Category.objects.create(name='Categoria Teste')
        self.product = Product.objects.create(name='Perfume Teste', brand=self.brand, category=self.category, fragrance='WO')
        self.sku = SKU.objects.create(sku_code='SKU-001', concentration='EDP', volume_ml=100, price=150.00, stock_quantity=10, product=self.product)

        self.cart = Cart.objects.create(user=self.customer)
        self.cart_item = CartItem.objects.create(cart=self.cart, sku=self.sku, quantity=2)

        self.checkout_url = reverse('orders:checkout')

    def teste_create_order_from_cart(self):
        '''
        Tests the checkout endpoint to ensure a valid cart generates a 'PENDING' order, 
        clears the cart items, and properly redirects the user to the payment gateway.
        '''
        payload = {
            'address': self.address.id
        }

        response = self.client.post(self.checkout_url, data=payload)

        self.assertEqual(response.status_code, 302)

        order_exists = Order.objects.filter(customer=self.customer, status='PENDING').exists()
        self.assertTrue(order_exists)

        cart_items_count = CartItem.objects.filter(cart=self.cart).count()
        self.assertEqual(cart_items_count, 0)

class OrderWerbhookTestCase(TestCase):
    '''
    Test suite for the asynchronous Mercado Pago webhook handler.
    Verifies the correct parsing of payloads and subsequent database updates.
    '''
    def setUp(self):
        '''
        Sets up an initial pending order to simulate an incoming payment approval.
        '''
        self.customer = Customer.objects.create(first_name='João', last_name='Teste', email='joao@teste.com')

        self.address = Address.objects.create(
            customer=self.customer, 
            street='Rua Teste', 
            number='123', 
            city='Laguna', 
            state='SC', 
            zip_code='88790-000'
        )

        self.order = Order.objects.create(
            customer=self.customer,
            address=self.address,
            status='PENDING',
            total_price=150.00
        )

        self.webhook_url = reverse('orders:webhook')

    @patch('apps.orders.views.MercadoPagoService')
    def test_mercado_pago_webhook_approved(self, MockMercadoPagoService):
        '''
        Mocks the Mercado Pago SDK response to simulate an 'approved' payment event.
        Verifies that the webhook correctly processes the payload and transitions 
        the order status to 'PAID'.
        '''
        mock_instance = MockMercadoPagoService.return_value
        mock_instance.sdk.payment.return_value.get.return_value = {
            'response': {
                'status': 'approved',
                'external_reference': str(self.order.id)
            }
        }

        payload = {
            'type': 'payment',
            'data': {'id': '123456789'}
        }

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()

        self.assertEqual(self.order.status, 'PAID')