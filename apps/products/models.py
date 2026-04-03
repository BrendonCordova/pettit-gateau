from django.db import models
from apps.base.models import BaseModel

class Category(BaseModel):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
class Brand(BaseModel):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name
class Product(BaseModel):

    class Fragrance(models.TextChoices):
        WOOD = "WO", "Wood"
        FLORAL = "FL", "Floral"
        CITRUS = "CI", "Citrus"
        ORIENTAL = "OR", "Oriental"
        FRUITY = "FR", "Fruity"

    name = models.CharField(max_length=120)
    description = models.TextField(max_length=600)
    fragrance = models.CharField(max_length=2, choices=Fragrance.choices)

    #Relationship
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

    def __str__(self):
        return f"{self.brand.name} - {self.name}"