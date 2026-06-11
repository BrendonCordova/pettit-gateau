from django.db import models
from django.contrib.auth import get_user_model
from apps.base.models import BaseModel
from apps.products.models import SKU
from decimal import Decimal

User = get_user_model()

class Coupon(BaseModel):
    '''Model to manage discount codes.'''
    code = models.CharField(max_length=50, unique=True, verbose_name='Código do Cupom')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Desconto em %')
    discount_fixed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Desconto Fixo (R$)')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    def __str__(self):
        return self.code

class Cart(BaseModel):
    '''
    Represents a shopping cart tied to a user or an anonymous session.
    Handles pricing logic including shipping calculations and coupon discounts.
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name='chave da sessão')
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Cupom Aplicado')

    cep = models.CharField(max_length=9, null=True, blank=True)
    shipping_name = models.CharField(max_length=100, null=True, blank=True)
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_days = models.PositiveIntegerField(default=0)

    @property
    def subtotal_price(self):
        '''Calculates the sum of all cart items before shipping and discounts.'''
        return sum(item.subtotal for item in self.items.all())

    @property
    def discount_amount(self):
        '''Calculates the discount to be applied based on the attached coupon.'''
        if not self.coupon:
            return Decimal('0.00')
        if self.coupon.discount_percentage:
            return (self.subtotal_price * self.coupon.discount_percentage) / Decimal('100.00')
        if self.coupon.discount_fixed:
            return self.coupon.discount_fixed
        return Decimal('0.00')

    @property
    def total_price(self):
        '''Calculates the final cart total ensuring it never drops below zero.'''
        total = (self.subtotal_price + self.shipping_price) - self.discount_amount
        return max(total, Decimal('0.00'))

    def __str__(self):
        if self.user:
            return f'Carrinho de {self.user.email}'
        return f'Carrinho de {self.session_key}'
    
    def merge_with_user_cart(self, user):
        '''
        Merges an anonymous session cart into the authenticated user's cart
        upon login, preserving items, coupons, and shipping details.
        '''
        user_cart, _ = Cart.objects.get_or_create(user=user)
        for item in self.items.all():
            user_item, created = CartItem.objects.get_or_create(cart=user_cart, sku=item.sku, defaults={'quantity': item.quantity})
            if not created:
                user_item.quantity += item.quantity
                user_item.save()
        if self.coupon: user_cart.coupon = self.coupon
        if self.cep: 
            user_cart.cep = self.cep
            user_cart.shipping_name = self.shipping_name
            user_cart.shipping_price = self.shipping_price
            user_cart.shipping_days = self.shipping_days
        user_cart.save()
        self.items.all().delete()
        self.delete()

class CartItem(BaseModel):
    '''
    Represents an individual SKU inside a shopping cart.
    '''
    cart = models.ForeignKey(Cart, on_delete=models.PROTECT, related_name='items')
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT, related_name='cart_item')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')

    @property
    def subtotal(self):
        '''Calculates the total price for this specific item based on its quantity.'''
        return self.sku.price * self.quantity

    def __str__(self):
        return f'{self.quantity}x {self.sku.product.name} ({self.sku.volume_ml}ml)'
    
