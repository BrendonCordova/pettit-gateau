from django.test import TestCase
from apps.products.models import Product, Brand, Category, Review
from apps.customers.models import Customer
from django.urls import reverse

class ProductReviewTestCase(TestCase):
    '''
    Test suite for product reviews functionality.
    Verifies the calculation of average ratings, review counts, 
    and the API endpoint for loading paginated reviews.
    '''

    def setUp(self):
        '''
        Sets up the initial database state for the test cases.
        Creates a mock brand, category, customers, product, and initial reviews.
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
        '''
        Tests if the get_average_rating method correctly calculates 
        the mean rating from all associated reviews.
        '''
        media = self.product.get_average_rating()

        self.assertEqual(media, 4.5)

    def test_get_reviews_count(self):
        '''
        Tests if the get_reviews_count method accurately returns 
        the total number of reviews for a product.
        '''
        total = self.product.get_reviews_count()

        self.assertEqual(total, 2)

    def test_load_more_reviews_api(self):
        '''
        Tests the asynchronous API endpoint for loading product reviews.
        Verifies the HTTP status code, the number of returned reviews, 
        pagination flags, and data serialization.
        '''
        url = reverse('products:api_reviews', kwargs={'slug': self.product.slug})

        response = self.client.get(f'{url}?page=1')

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data['reviews']), 2)

        self.assertFalse(data['has_next'])

        self.assertEqual(data['reviews'][0]['customer'], 'Maria')