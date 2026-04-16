from django.db import models
from django.utils.text import slugify
from apps.base.models import BaseModel

class Category(BaseModel):
    name = models.CharField(max_length=80, verbose_name="Nome da Categoria")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
class Brand(BaseModel):
    name = models.CharField(max_length=80, verbose_name="Nome da Marca")

    def __str__(self):
        return self.name
class Product(BaseModel):

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
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
class SKU(BaseModel):
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