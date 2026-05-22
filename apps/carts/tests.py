from django.test import TestCase
import json
from django.urls import reverse
from apps.products.models import Product, Brand, Category, SKU
from apps.customers.models import Customer
from .models import Cart

class CartAPITestCase(TestCase):

    def setUp(self):
        self.brand = Brand.objects.create(name='Marca Teste')
        self.category = Category.objects.create(name='Categoria Teste')
        self.product = Product.objects.create(
            name='Perfume Teste', brand=self.brand, category=self.category, fragrance='WO'
        )

        self.sku = SKU.objects.create(
            sku_code='SKU-001',
            concentration='EDP',
            volume_ml=100,
            price=100.00,
            stock_quantity=5,
            product=self.product
        )

        self.customer = Customer.objects.create(first_name='João', last_name='TESTE', email='joao@teste.com')
        self.client.force_login(self.customer)

        self.add_url = reverse('carts:cart-api')

    def test_add_item_to_cart_success(self):

        payload = {
            'sku_id': str(self.sku.id),
            'quantity': 2
        }

        response = self.client.post(
            self.add_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        cart = Cart.objects.get(user=self.customer)
        self.assertEqual(cart.items.count(), 1)

    def test_add_item_exceeding_stock(self):
        payload = {
            'sku_id': str(self.sku.id),
            'quantity': 10
        }

        response = self.client.post(
            self.add_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)