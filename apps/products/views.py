from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Brand, Category
from django.core.paginator import Paginator
from django.db.models import Q
from apps.orders.models import Order
from .forms import ReviewForm, Review
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages

def product_list(request):

    products = Product.objects.prefetch_related('skus').filter(is_active=True).order_by('-created_at')

    brand_id = request.GET.get('brand')
    category_id = request.GET.get('category')
    fragrance = request.GET.get('fragrance')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('q')

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

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

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

    if not product.is_active:
        messages.warning(request, f'O perfume {product.name} não está disponível no momento. Que tal escolher outra fragrância?')

        return redirect('products:list')

    all_reviews = product.reviews.all().order_by('-created_at')
    recent_reviews = all_reviews[:3]
    reviews_count = all_reviews.count()

    user_has_purchased = False
    existing_review = None

    available_skus = product.skus.filter(is_active=True)
    default_sku = available_skus.first()

    if request.user.is_authenticated:
        user_has_purchased = Order.objects.filter(
            customer=request.user,
            status='PAID',
            items__sku__product=product
        ).exists()

        existing_review = Review.objects.filter(product=product, customer=request.user).first()

    if request.method == 'POST' and user_has_purchased:
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.customer = request.user
            review.save()
            return redirect('products:detail', slug=product.slug)
    else:
        form = ReviewForm(instance=existing_review)

    context = {
        'product': product,
        'reviews': recent_reviews,
        'reviews_count': reviews_count,
        'form': form,
        'user_has_purchased': user_has_purchased,
        'skus': available_skus,
        'default_sku': default_sku,
    }
    return render(request, 'products/product_detail.html', context)

def load_more_reviews_api(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    all_reviews = product.reviews.all().order_by('-created_at')

    paginator = Paginator(all_reviews, 3)

    page_number = request.GET.get('page', 2)

    try:
        page_obj = paginator.page(page_number)
    except Exception:
        return JsonResponse({'reviews': [], 'has_next': False})
    
    reviews_data = []
    for review in page_obj:
        reviews_data.append({
            'customer': review.customer.first_name,
            'rating': review.rating,
            'comment': review.comment or '',
        })
    
    return JsonResponse({
        'reviews': reviews_data,
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
    })