from django.test import TestCase
from apps.products.models import Product, Brand, Category, Review
from apps.customers.models import Customer
from django.urls import reverse

class ProductReviewTestCase(TestCase):

    def setUp(self):
        '''
        Arrange
        '''
        self.brand = Brand.objects.create(name='Marca Teste')
        self.category = Category.objects.create(name='Categoria Teste')

        self.customer1 = Customer.objects.create(first_name='João', last_name='Teste', email='joao@teste.com')
        self.customer2 = Customer.objects.create(first_name='Maria', last_name='Teste', email='maria@teste.com')

        self.product = Product.objects.create(
            name='Perfume Teste',
            description='Descrição teste',
            fragrance='WO',
            brand=self.brand,
            slug='TESTE-PRODUTO',
            category=self.category
        )

        Review.objects.create(product=self.product, customer=self.customer1, rating=5, comment='Excelente!')
        Review.objects.create(product=self.product, customer=self.customer2, rating=4, comment='Bom demais!')

    def test_get_average_rating(self):
        media = self.product.get_average_rating()

        self.assertEqual(media, 4.5)

    def test_get_reviews_count(self):
        total = self.product.get_reviews_count()

        self.assertEqual(total, 2)

    def test_load_more_reviews_api(self):
        url = reverse('products:api_reviews', kwargs={'slug': self.product.slug})

        response = self.client.get(f'{url}?page=1')

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data['reviews']), 2)

        self.assertFalse(data['has_next'])

        self.assertEqual(data['reviews'][0]['customer'], 'Maria')