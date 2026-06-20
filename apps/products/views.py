from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Brand, Category, Banner, SKU, Fragrance, Concentration
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from apps.orders.models import Order
from .forms import ReviewForm, Review
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.utils import timezone
from django.db.models.functions import Coalesce
from apps.carts.models import Coupon
from django.db.models import ProtectedError

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
        products = products.annotate(
            avg_rating=Coalesce(Avg('reviews__rating'), 0.0)
        ).order_by('-avg_rating', '-created_at')
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

@staff_member_required(login_url='/conta/login/')
def admin_inventory_view(request):
    '''
    Renders the custom inventory management dashboard for staff members.
    Handles complex filtering, sorting, and search functionality for SKUs, 
    and passes related entities (Categories, Brands, Banners, Coupons) to the UI.
    '''
    skus = SKU.objects.select_related('product').all()

    search_query = request.GET.get('q', '')
    if search_query:
        skus = skus.filter(
            Q(product__name__icontains=search_query) | 
            Q(sku_code__icontains=search_query)
        )

    sort_by = request.GET.get('sort', 'id_asc')
    
    if sort_by == 'price_desc':
        skus = skus.order_by('-price')
    elif sort_by == 'price_asc':
        skus = skus.order_by('price')
    elif sort_by == 'newest':
        skus = skus.order_by('-created_at')
    elif sort_by == 'name_asc':
        skus = skus.order_by('product__name')
    elif sort_by == 'name_desc':
        skus = skus.order_by('-product__name')
    elif sort_by == 'id_desc':
        skus = skus.order_by('-id')
    elif sort_by == 'sku_asc':
        skus = skus.order_by('sku_code')
    elif sort_by == 'sku_desc':
        skus = skus.order_by('-sku_code')
    elif sort_by == 'volume_asc':
        skus = skus.order_by('volume_ml')
    elif sort_by == 'volume_desc':
        skus = skus.order_by('-volume_ml')
    elif sort_by == 'stock_asc':
        skus = skus.order_by('stock_quantity')
    elif sort_by == 'stock_desc':
        skus = skus.order_by('-stock_quantity')
    else:
        skus = skus.order_by('id')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    banners = Banner.objects.all().order_by('-created_at')
    fragrances = Fragrance.objects.all().order_by('name')
    concentrations = Concentration.objects.all().order_by('name')
    coupons = Coupon.objects.all().order_by('-created_at')
    products_list = Product.objects.all().order_by('name')

    context = {
        'skus': skus,
        'search_query': search_query,
        'current_sort': sort_by,
        'categories': categories,
        'brands': brands,
        'fragrances': fragrances,
        'concentrations': concentrations,
        'banners': banners,
        'coupons': coupons,
        'products_list': products_list
    }
    return render(request, 'products/admin_inventory.html', context)

@staff_member_required(login_url='/conta/login/')
@transaction.atomic
def add_product_quick_view(request):
    '''
    Handles the creation of a new Product and its initial SKU from the admin dashboard.
    Ensures SKU uniqueness, processes the main product image upload, 
    and wraps the creation in a database transaction to prevent orphaned data.
    '''
    if request.method == 'POST':
        try:
            sku_code = request.POST.get('sku_code')
            if SKU.objects.filter(sku_code=sku_code).exists():
                messages.error(request, f"O SKU '{sku_code}' já existe no sistema! Tente outro.")
                return redirect('products:admin-inventory')

            name = request.POST.get('name')
            description = request.POST.get('description')
            fragrance = request.POST.get('fragrance')
            category = get_object_or_404(Category, id=request.POST.get('category'))
            brand = get_object_or_404(Brand, id=request.POST.get('brand'))

            produto = Product.objects.create(
                name=name,
                description=description,
                fragrance_id=request.POST.get('fragrance'),
                category=category,
                brand=brand
            )

            raw_price = request.POST.get('price', '0').replace('R$', '').replace(' ', '')
            if '.' in raw_price and ',' in raw_price:
                clean_price = raw_price.replace('.', '').replace(',', '.')
            else:
                clean_price = raw_price.replace(',', '.')

            SKU.objects.create(
                product=produto,
                sku_code=sku_code,
                concentration_id=request.POST.get('concentration'),
                volume_ml=request.POST.get('volume_ml'),
                price=clean_price,
                stock_quantity=request.POST.get('stock_quantity')
            )

            image_file = request.FILES.get('image')
            if image_file:
                from .models import ProductImage
                ProductImage.objects.create(
                    product=produto,
                    image=image_file,
                    is_main=True,
                    display_order=0
                )

            messages.success(request, f"Produto '{name}' salvo com sucesso!")
            
        except Exception as e:
            print(f"ERRO AO SALVAR PRODUTO: {e}")
            messages.error(request, "Erro ao salvar o produto. Verifique se preencheu todos os campos corretamente.")

    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def add_brand_quick_view(request):
    '''
    Creates a new Brand entity directly from the inventory dashboard modal.
    '''
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            brand, created = Brand.objects.get_or_create(name=name.strip())
            if created:
                messages.success(request, f"Marca '{brand.name}' cadastrada com sucesso!")
            else:
                messages.warning(request, f"A marca '{brand.name}' já existe no sistema.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def add_category_quick_view(request):
    '''
    Creates a new Category entity directly from the inventory dashboard modal.
    '''
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category, created = Category.objects.get_or_create(name=name.strip())
            if created:
                messages.success(request, f"Categoria '{category.name}' cadastrada com sucesso!")
            else:
                messages.warning(request, f"A categoria '{category.name}' já existe no sistema.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
@transaction.atomic
def edit_product_quick_view(request, sku_id):
    '''
    Updates an existing Product and its specific SKU details.
    Handles dynamic image deletions, new image uploads, and ensures 
    the updated SKU code remains unique within the system.
    '''
    if request.method == 'POST':
        try:
            sku = get_object_or_404(SKU, id=sku_id)
            produto = sku.product

            new_sku_code = request.POST.get('sku_code')
            if new_sku_code != sku.sku_code and SKU.objects.filter(sku_code=new_sku_code).exists():
                messages.error(request, f"O código SKU '{new_sku_code}' já está a ser usado! Alterações não salvas.")
                return redirect('products:admin-inventory')

            produto.name = request.POST.get('name')
            produto.description = request.POST.get('description')
            produto.fragrance_id = request.POST.get('fragrance')
            produto.category = get_object_or_404(Category, id=request.POST.get('category'))
            produto.brand = get_object_or_404(Brand, id=request.POST.get('brand'))
            produto.is_active = request.POST.get('product_is_active') == 'on'
            produto.save()

            sku.sku_code = new_sku_code
            sku.concentration_id = request.POST.get('concentration')
            sku.volume_ml = request.POST.get('volume_ml')
            
            sku.is_active = request.POST.get('is_active') == 'on'
            
            raw_price = request.POST.get('price', '0').replace('R$', '').replace(' ', '')
            if '.' in raw_price and ',' in raw_price:
                sku.price = raw_price.replace('.', '').replace(',', '.')
            else:
                sku.price = raw_price.replace(',', '.')
                
            sku.stock_quantity = request.POST.get('stock_quantity')
            sku.save()

            images_to_delete = request.POST.getlist('delete_images')
            if images_to_delete:
                from .models import ProductImage
                ProductImage.objects.filter(id__in=images_to_delete, product=produto).delete()

            image_file = request.FILES.get('image')
            if image_file:
                from .models import ProductImage
                has_main = ProductImage.objects.filter(product=produto, is_main=True).exists()
                ProductImage.objects.create(
                    product=produto,
                    image=image_file,
                    is_main=not has_main,
                    display_order=0
                )

            messages.success(request, f"Variação '{sku.sku_code}' atualizada com sucesso!")
        except Exception as e:
            print(f"ERRO AO EDITAR PRODUTO: {e}")
            messages.error(request, "Erro ao editar o produto. Verifique os dados inseridos.")

    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def toggle_banner_view(request, banner_id):
    '''
    Activates the selected promotional banner and automatically deactivates 
    all other banners, ensuring only one campaign is displayed on the storefront at a time.
    '''
    if request.method == 'POST':
        banner = get_object_or_404(Banner, id=banner_id)
        
        Banner.objects.all().update(is_active=False)
        
        banner.is_active = True
        banner.save()
        messages.success(request, 'Propaganda da página inicial atualizada com sucesso!')
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def delete_banner_view(request, banner_id):
    '''
    Permanently removes a promotional banner from the system's history.
    '''
    if request.method == 'POST':
        banner = get_object_or_404(Banner, id=banner_id)
        banner.delete()
        messages.success(request, 'Banner removido do histórico.')
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def add_banner_inventory_view(request):
    '''
    Uploads and creates a new promotional banner.
    Automatically sets the new banner as the active storefront campaign upon creation.
    '''
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            Banner.objects.all().update(is_active=False)
            
            Banner.objects.create(
                title=f"Campanha {timezone.now().strftime('%d/%m/%Y')}",
                image=image,
                is_active=True
            )
            messages.success(request, 'Novo banner adicionado e ativado na loja!')
        else:
            messages.error(request, 'Por favor, selecione uma imagem.')
            
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def add_coupon_view(request):
    '''
    Creates a new discount coupon from the inventory dashboard.
    Supports both fixed-value (currency) and percentage-based discounts.
    '''
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type')
        value = request.POST.get('value')
        
        if not code or not value:
            messages.error(request, 'Código e valor são obrigatórios.')
            return redirect('products:admin-inventory')
            
        try:
            value = float(str(value).replace(',', '.'))
            
            if discount_type == 'percent':
                Coupon.objects.create(code=code, discount_percentage=value)
            else:
                Coupon.objects.create(code=code, discount_fixed=value)
                
            messages.success(request, f'Cupom {code} criado com sucesso!')
        except Exception as e:
            messages.error(request, 'Erro. Verifique se o código já existe.')
            
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def toggle_coupon_view(request, coupon_id):
    '''
    Toggles the active status (enabled/disabled) of a promotional discount coupon.
    '''
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        coupon.is_active = not coupon.is_active
        coupon.save()
        status_txt = "ativado" if coupon.is_active else "desativado"
        messages.success(request, f'Cupom {coupon.code} {status_txt}!')
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
@transaction.atomic
def add_variation_view(request):
    ''' Adds a new SKU (size variation) '''
    if request.method == 'POST':
        try:
            sku_code = request.POST.get('sku_code')
            if SKU.objects.filter(sku_code=sku_code).exists():
                messages.error(request, f"O SKU '{sku_code}' já existe! Tente outro.")
                return redirect('products:admin-inventory')

            produto = get_object_or_404(Product, id=request.POST.get('product_id'))

            raw_price = request.POST.get('price', '0').replace('R$', '').replace(' ', '')
            clean_price = raw_price.replace('.', '').replace(',', '.') if '.' in raw_price and ',' in raw_price else raw_price.replace(',', '.')

            SKU.objects.create(
                product=produto,
                sku_code=sku_code,
                concentration_id=request.POST.get('concentration'),
                volume_ml=request.POST.get('volume_ml'),
                price=clean_price,
                stock_quantity=request.POST.get('stock_quantity')
            )
            messages.success(request, f"Nova variação de {request.POST.get('volume_ml')}ml adicionada ao perfume {produto.name}!")
        except Exception as e:
            messages.error(request, "Erro ao adicionar variação. Verifique os dados.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def edit_brand_view(request, brand_id):
    ''' Update the name of an existing brand. '''
    if request.method == 'POST':
        brand = get_object_or_404(Brand, id=brand_id)
        new_name = request.POST.get('name', '').strip()
        if new_name:
            brand.name = new_name
            brand.save()
            messages.success(request, f"Marca atualizada para '{brand.name}'.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def delete_brand_view(request, brand_id):
    ''' Exclude a brand if there are no products associated with it. '''
    if request.method == 'POST':
        brand = get_object_or_404(Brand, id=brand_id)
        try:
            name = brand.name
            brand.delete()
            messages.success(request, f"Marca '{name}' excluída com sucesso.")
        except ProtectedError:
            messages.error(request, f"A marca '{brand.name}' não pode ser excluída pois existem perfumes vinculados a ela.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def edit_category_view(request, category_id):
    ''' Update the name of an existing category. '''
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        new_name = request.POST.get('name', '').strip()
        if new_name:
            category.name = new_name
            category.save()
            messages.success(request, f"Categoria atualizada para '{category.name}'.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def delete_category_view(request, category_id):
    ''' Delete a category if there are no products associated with it. '''
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        try:
            name = category.name
            category.delete()
            messages.success(request, f"Categoria '{name}' excluída com sucesso.")
        except ProtectedError:
            messages.error(request, f"A categoria '{category.name}' não pode ser excluída pois existem perfumes vinculados a ela.")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def add_fragrance_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Fragrance.objects.get_or_create(name=name.strip())
            messages.success(request, f"Fragrância '{name}' cadastrada com sucesso!")
    return redirect('products:admin-inventory')

@staff_member_required(login_url='/conta/login/')
def add_concentration_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Concentration.objects.get_or_create(name=name.strip())
            messages.success(request, f"Concentração '{name}' cadastrada com sucesso!")
    return redirect('products:admin-inventory')