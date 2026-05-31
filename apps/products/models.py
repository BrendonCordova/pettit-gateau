from django.db import models
from django.utils.text import slugify
from apps.base.models import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.customers.models import Customer
from django.db.models import Avg

class Category(BaseModel):
    '''
    Represents a product category to group related items.
    '''
    name = models.CharField(max_length=80, verbose_name="Nome da Categoria")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
class Brand(BaseModel):
    '''
    Represents the manufacturer or brand of a product.
    '''
    name = models.CharField(max_length=80, verbose_name="Nome da Marca")

    def __str__(self):
        return self.name
class Product(BaseModel):
    '''
    Core model representing a unique fragrance item.
    Contains general details like name, description, and fragrance family.
    Acts as the parent entity for specific SKUs and Images.
    '''
    class Fragrance(models.TextChoices):
        WOOD = "WO", "Wood"
        FLORAL = "FL", "Floral"
        CITRUS = "CI", "Citrus"
        ORIENTAL = "OR", "Oriental"
        FRUITY = "FR", "Fruity"

    name = models.CharField(max_length=120, verbose_name="Nome do Produto")
    description = models.TextField(max_length=600, verbose_name="Descrição")
    fragrance = models.CharField(max_length=2, choices=Fragrance.choices, verbose_name="Fragrância")
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name="Slug (URL)")

    #Relationship
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

    def __str__(self):
        return f"{self.brand.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        '''
        Overrides the default save method to auto-generate a slug 
        from the product name if one is not provided.
        '''
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_average_rating(self):
        '''
        Calculates the average rating from all reviews associated with this product.

        Returns:
            float: The average rating rounded to one decimal place, 
                   or 0 if no reviews exist.
        '''
        average = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(average, 1) if average else 0
    
    def get_reviews_count(self):
        '''
        Counts the total number of reviews submitted for this product.

        Returns:
            int: The total review count.
        '''
        return self.reviews.count()
    
class SKU(BaseModel):
    '''
    Represents a specific Stock Keeping Unit (SKU) for a product.
    Defines unique variations based on concentration and volume, 
    tracking individual pricing and inventory levels.
    '''
    class Concentration(models.TextChoices):
        EDC = "EDC", "Eau de Cologne"
        EDT = "EDT", "Eau de Toilette"
        EDP = "EDP", "Eau de Parfum"
        PARFUM = "PAR", "Parfum"

    sku_code = models.CharField(max_length=50, unique=True, verbose_name="Código SKU")
    concentration = models.CharField(max_length=3, choices=Concentration.choices, verbose_name="Concentração")
    volume_ml = models.PositiveIntegerField(verbose_name="Volume em ml")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Quantidade em Estoque")

    # Relationship
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="skus")

    class Meta:
        verbose_name_plural = "SKUs"

    def __str__(self):
        return f"{self.product.name} - {self.volume_ml} - R$ {self.price}"
    
class ProductImage(BaseModel):
    '''
    Handles the visual assets for a product.
    Supports multiple ordered images and designates a main display image.
    '''
    image = models.ImageField(upload_to="products/%Y/%m/%d/", verbose_name="Imagem")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")
    is_main = models.BooleanField(default=False, verbose_name="Imagem Principal")

    #Relationship
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    class Meta:
        ordering = ['display_order']
        verbose_name = "Imagem do Produto"
        verbose_name_plural = "Imagens do Produto"

    def __str__(self):
        return f"Imagem de {self.product.name}"
    
class Review(BaseModel):
    '''
    Stores customer feedback and ratings for specific products.
    Enforces a unique constraint to prevent multiple reviews 
    from the same customer on a single product.
    '''
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Nota')
    comment = models.TextField(blank=True, null=True, verbose_name='Comentário')
    # Relationships
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews', verbose_name='Produto')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews', verbose_name='Cliente')

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-created_at']
        unique_together = ('product', 'customer')

    def __str__(self):
        return f'{self.customer.first_name} - {self.product.name} ({self.rating}/5)'
    
class Banner(BaseModel):
    '''
    Model for managing promotional banners on the homepage.
    Images are uploaded to the media directory.
    '''
    title = models.CharField(max_length=100, verbose_name="Título da Campanha")
    image = models.ImageField(upload_to="banners/%Y/%m/", verbose_name="Imagem do Banner (Desktop)")
    link = models.URLField(blank=True, null=True, verbose_name="Link de Redirecionamento")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['-created_at']

    def __str__(self):
        return self.title