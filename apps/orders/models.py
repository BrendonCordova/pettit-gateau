from django.db import models
from apps.base.models import BaseModel
from apps.customers.models import Customer, Address
from apps.products.models import SKU
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from decimal import Decimal
from django.core.validators import MinValueValidator
from datetime import timedelta

class ShippingMethod(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Nome da Transportadora (Ex: PAC, Sedex)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Preço do Frete")
    delivery_days = models.PositiveIntegerField(default=7, verbose_name="Prazo de Entrega (Dias)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = 'Método de Envio'
        verbose_name_plural = 'Métodos de Envio'

    def __str__(self):
        return f"{self.name} ({self.delivery_days} dias) - R$ {self.price}"
class Order(BaseModel):
    '''
    Represents a customer's purchase order.
    Tracks the lifecycle status of the transaction (e.g., PENDING, PAID, SHIPPED) 
    and maintains the total financial value of the order.
    '''
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
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Transportadora')
    payment_approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de Aprovação do Pagamento')

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.id} - {self.customer.first_name} ({self.get_status_display()})'
    
    def update_total(self):
        '''
        Dynamically calculates and updates the order's total price based on 
        the sum of all associated order items' subtotals.
        '''
        total_items = sum(item.get_subtotal() for item in self.items.all())
        frete = self.shipping_method.price if self.shipping_method else Decimal('0.00')
        self.total_price = total_items + frete
        self.save()

    @property
    def expected_delivery_date(self):
        '''Calcula a data dinamicamente com base nos dias definidos no Admin pela Transportadora'''
        days = self.shipping_method.delivery_days if self.shipping_method else 7

        base_date = self.payment_approved_at if self.payment_approved_at else self.created_at

        if self.created_at:
            return self.created_at + timedelta(days=days)
        return None
    
class OrderItem(BaseModel):
    '''
    Represents a specific product SKU line within an order.
    Snapshots the price at the moment of purchase to prevent historical data 
    changes if the base product price is updated later.
    '''
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
        '''
        Calculates the financial subtotal for this specific order line.

        Returns:
            Decimal: The item's purchase price multiplied by its quantity.
        '''
        if self.price and self.quantity:
            return self.price * self.quantity
        return Decimal(0.00)
    
    def save(self, *args, **kwargs):
        '''
        Overrides the save method to automatically snapshot the SKU's current price 
        if a price is not explicitly provided during creation.
        '''
        if not self.price and self.sku:
            self.price = self.sku.price

        super().save(*args,**kwargs)

@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    '''
    Django Signal receiver that listens for the creation, update, or deletion 
    of OrderItems and triggers the parent Order to recalculate its total price.

    Args:
        sender (Model): The model class sending the signal (OrderItem).
        instance (OrderItem): The specific instance being saved or deleted.
        **kwargs: Additional keyword arguments passed by the signal.
    '''
    if instance.order:
        instance.order.update_total()