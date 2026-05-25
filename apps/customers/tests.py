from django.test import TestCase
from django.urls import reverse
from .models import Customer, Address

class CustomerModelTestCase(TestCase):
    def test_create_normal_user(self):

        user = Customer.objects.create_user(
            email='cliente@teste.com',
            password='senha_segura*',
            first_name='Cliente',
            last_name='Teste'
        )

        self.assertEqual(user.email, 'cliente@teste.com')
        self.assertTrue(user.check_password('senha_segura*'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = Customer.objects.create_superuser(
            email='admin@teste.com',
            password='senha_segura*',
            first_name='Admin',
            last_name='Chefe'
        )
        
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

class CustomerViewsTestCase(TestCase):
    def setUp(self):
        self.address_url = reverse('customers:address-create')
        self.customer = Customer.objects.create_user(
            email='joao@teste.com',
            password='senha_segura*',
            first_name='Joao',
            last_name='Teste'
        )

    def test_address_create_unauthenticated_blocked(self):
        response = self.client.get(self.address_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_address_create_authenticated_success(self):
        self.client.login(email='joao@teste.com', password='senha_segura*')

        payload = {
            'name': 'Minha Casa',
            'zip_code': '88790-000',
            'street': 'Rua dos Testes',
            'number': '123',
            'neighborhood': 'Centro',
            'city': 'Laguna',
            'state': 'SC',
            'is_default': True
        }

        response = self.client.post(self.address_url, data=payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('orders:checkout'))

        saved_address = Address.objects.filter(customer=self.customer, name='Minha Casa').exists()
        self.assertTrue(saved_address)