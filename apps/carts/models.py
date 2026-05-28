from django.db import models
from django.contrib.auth import get_user_model
from apps.base.models import BaseModel
from apps.products.models import SKU

User = get_user_model()

class Cart(BaseModel):
    '''
    Represents a shopping cart, acting as a container for selected products.
    Can be linked to an authenticated user or an anonymous session.
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name='chave da sessão')

    @property
    def total_price(self):
        '''
        Calculates the dynamic total price of all items currently in the cart.

        Returns:
            Decimal: The sum of the subtotals of all cart items.
        '''
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        if self.user:
            return f'Carrinho de {self.user.email}'
        return f'Carrinho de {self.session_key}'

class CartItem(BaseModel):
    '''
    Represents an individual SKU added to a specific shopping cart.
    Tracks the selected quantity for the transaction.
    '''
    cart = models.ForeignKey(Cart, on_delete=models.PROTECT, related_name='items')
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT, related_name='cart_item')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')

    @property
    def subtotal(self):
        '''
        Calculates the total cost for this specific item line.

        Returns:
            Decimal: The item price multiplied by the requested quantity.
        '''
        return self.sku.price * self.quantity

    def __str__(self):
        return f'{self.quantity}x {self.sku.product.name} ({self.sku.volume_ml}ml)'
    
