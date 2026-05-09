from django.db import models
from apps.base.models import BaseModel
from apps.customers.models import Customer, Address
from apps.products.models import SKU
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from decimal import Decimal
from django.core.validators import MinValueValidator

class Order(BaseModel):

    STATUS_CHOICE = (
        ('PENDING', 'Aguardando Pagamento'),
        ('PAID', 'Pagamento Aprovado'),
        ('PREPARING', 'Em Preparação'),
        ('SHIPPED', 'Enviado'),
        ('DELIVERED', 'Entregue'),
        ('CANCELED', 'Cancelado'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICE, default='PENDING', verbose_name='Status')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Preço Total')

    # Relationships
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders', verbose_name='Cliente')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders', verbose_name='Endereço de Entrega')

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.id} - {self.customer.first_name} ({self.get_status_display()})'
    
    def update_total(self):

        total = sum(item.get_subtotal() for item in self.items.all())
        self.total_price = total
        self.save()
    
class OrderItem(BaseModel):

    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True,verbose_name='Preço Unitário na Compra')
    quantity = models.PositiveIntegerField(verbose_name='Quantity', validators=[MinValueValidator(1)])

    # Relationships
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT, verbose_name='SKU do Produto')

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.quantity}x - {self.sku.product.name} ({self.sku.volume_ml}ml) - Pedido #{self.id}'
    
    def get_subtotal(self):
        if self.price and self.quantity:
            return self.price * self.quantity
        return Decimal(0.00)
    
    def save(self, *args, **kwargs):
        if not self.price and self.sku:
            self.price = self.sku.price

        super().save(*args,**kwargs)

@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    if instance.order:
        instance.order.update_total()