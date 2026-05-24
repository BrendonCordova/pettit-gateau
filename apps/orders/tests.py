from django.test import TestCase
from django.urls import reverse
from apps.customers.models import Customer, Address
from apps.products.models import Product, Brand, Category, SKU
from apps.carts.models import Cart, CartItem
from .models import Order
from unittest.mock import patch
import json

class OrderCreationTestCase(TestCase):

    def setUp(self):
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
    def setUp(self):

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