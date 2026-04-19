from django.shortcuts import render, get_object_or_404
from .models import Product, Brand, Category
from django.core.paginator import Paginator
from django.http import HttpResponse

def product_list(request):

    products = Product.objects.prefetch_related('skus').order_by('-created_at')

    brand_id = request.GET.get('brand')
    category_id = request.GET.get('category')
    fragrance = request.GET.get('fragrance')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if brand_id:
        products = products.filter(brand_id=brand_id)

    if category_id:
        products = products.filter(category_id=category_id)

    if fragrance:
        products = products.filter(fragrance=fragrance)

    if min_price:
        products = products.filter(skus__price__gte=min_price).distinct()

    if max_price:
        products = products.filter(skus__price__lte=max_price).distinct()

    paginator = Paginator(products, 8)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    query_dict = request.GET.copy()
    if 'page' in query_dict:
        del query_dict['page']
    query_string = query_dict.urlencode()

    context = {
        'page_obj': page_obj,
        'brands': Brand.objects.all(),
        'categories': Category.objects.all(),
        'fragrance_choices': Product.Fragrance.choices,
        'current_filters': request.GET,
        'query_string': query_string,
    }  
    return render(request, 'products/product_list.html', context)

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