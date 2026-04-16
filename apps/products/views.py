from django.shortcuts import render, get_object_or_404
from .models import Product
from django.http import HttpResponse

def product_detail(request, slug):

    product = get_object_or_404(Product.objects.prefetch_related('skus'), slug=slug)

    available_skus = product.skus.filter(is_active=True)
    default_sku = available_skus.first()

    context = {
        'product': product,
        'skus': available_skus,
        'default_sku': default_sku,
    }
    return render(request, 'products/product_detail.html', context)