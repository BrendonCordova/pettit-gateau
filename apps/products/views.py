from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Brand, Category, Banner
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from apps.orders.models import Order
from .forms import ReviewForm, Review
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages

def product_list(request, category_name=None):
    '''
    Retrieves and displays a paginated list of active products, 
    with optional filtering by brand, category, fragrance, price range, and search terms.

    Args:
        request (HttpRequest): The HTTP request object containing GET parameters 
                               for filtering and pagination.

    Returns:
        HttpResponse: The rendered 'product_list.html' template containing the 
                      filtered products and context data.
    '''
    products = Product.objects.prefetch_related('skus', 'images').filter(is_active=True)

    page_title = "Nossas Fragrâncias"

    if category_name:
        products = products.filter(category__name__iexact=category_name)
        
        if category_name.lower() in ['masculino', 'feminino']:
            page_title = f"Perfumes {category_name.capitalize()}s"
        else:
            page_title = f"Perfumes {category_name.capitalize()}"

    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        ).distinct()

    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'a-z':
        products = products.order_by('name')
    elif sort_by == 'z-a':
        products = products.order_by('-name')
    elif sort_by == 'top_rated':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating', '-created_at')
    elif sort_by == 'best_selling':
        products = products.annotate(num_reviews=Count('reviews')).order_by('-num_reviews', '-created_at')
    else: 
        products = products.order_by('-created_at')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_dict = request.GET.copy()
    if 'page' in query_dict:
        del query_dict['page']
    query_string = query_dict.urlencode()

    context = {
        'page_obj': page_obj,
        'current_filters': request.GET,
        'query_string': query_string,
        'page_title': page_title,
    }  
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    '''
    Displays the details of a specific product based on its slug.
    Handles product review submissions if the authenticated user has purchased the item.

    Args:
        request (HttpRequest): The HTTP request object.
        slug (str): The unique URL slug of the product.

    Returns:
        HttpResponse: The rendered 'product_detail.html' template with product data, 
                      available SKUs, and reviews. Redirects to the product list 
                      if the product is inactive.
    '''
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
    '''
    Provides a paginated JSON response of reviews for a specific product, 
    used for the asynchronous "load more" functionality on the frontend.

    Args:
        request (HttpRequest): The HTTP request object containing the 'page' parameter.
        slug (str): The unique URL slug of the product.

    Returns:
        JsonResponse: A JSON object containing a list of serialized reviews 
                      and pagination metadata (e.g., has_next).
    '''
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

def home_view(request):
    '''
    Renders the e-commerce homepage.
    Fetches the active promotional banner, top 4 best-selling products, and 4 newest arrivals.
    '''
    active_banner = Banner.objects.filter(is_active=True).first()

    best_sellers = Product.objects.prefetch_related('skus', 'images').filter(is_active=True).annotate(
        num_reviews=Count('reviews')
    ).order_by('-num_reviews', '-created_at')[:4]

    newest = Product.objects.prefetch_related('skus', 'images').filter(is_active=True).order_by('-created_at')[:4]

    context = {
        'banner': active_banner,
        'best_sellers': best_sellers,
        'newest': newest,
    }
    return render(request, 'products/home.html', context)