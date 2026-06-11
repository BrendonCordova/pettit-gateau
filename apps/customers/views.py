from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .forms import CustomerCreationForm, AddressForm, CustomerUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from .models import Customer
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Address
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from apps.carts.models import Cart
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

@login_required
def address_create_view(request):
    '''
    Handles the creation of a new shipping or billing address for an authenticated user.
    Upon successful creation, redirects the user back to the checkout process.

    Args:
        request (HttpRequest): The HTTP request object containing the form data.

    Returns:
        HttpResponse: The rendered 'address_form.html' template or a redirection 
                      to the checkout view.
    '''
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = request.user
            address.save()

            return redirect('orders:checkout')
    else:
        form = AddressForm()

    return render(request, 'customers/address_form.html', {'form': form})

class CustomerLoginView(LoginView):
    '''
    Class-based view handling customer authentication.
    Overrides the default Django template, handles cart merging for anonymous users,
    and automatically redirects to the appropriate URL after login.
    '''
    template_name = 'customers/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        '''
        Processes the valid login form and merges any anonymous shopping cart 
        into the authenticated user's account.
        '''
        session_key = self.request.session.session_key

        response = super().form_valid(form)

        if session_key:
            try:
                anon_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                anon_cart.merge_with_user_cart(self.request.user)
            except Cart.DoesNotExist:
                pass

        return response

        '''
        '''
    def get_success_url(self):
        '''
        Redirects the user to the correct page after login.
        If they came from the shopping cart (parameter ?next=), returns to the checkout page.
        '''
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
            
        return reverse_lazy('customers:profile')

def register_view(request):
    '''
    Processes new customer registrations.
    Creates an inactive user account, generates a secure cryptographic token,
    and dispatches an account activation email.

    Args:
        request (HttpRequest): The HTTP request object containing registration data.

    Returns:
        HttpResponse: The rendered 'register.html' template on GET or validation failure, 
                      or a redirection to the login page upon successful registration.
    '''
    if request.method == 'POST':
        form = CustomerCreationForm(request.POST)
        if form.is_valid():
            
            user = form.save(commit=False)

            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            verification_link = request.build_absolute_uri(
                reverse('customers:verify-email', kwargs={'uidb64': uid, 'token': token})
            )

            context = {
                'user': user,
                'verification_link': verification_link
            }

            html_content = render_to_string('customers/emails/verification_email.html', context)
            text_content = strip_tags(html_content)

            subject = 'Confirme sua conta no Pettit Gateau!'
            
            send_mail(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_content,
                fail_silently=False,
            )

            messages.success(request, 'Conta criada com sucesso! Verifique seu e-mail para ativar seu cadastro.')
            return redirect('customers:login')
        else:
            print("\n--- ERROS DE VALIDAÇÃO DO FORMULÁRIO ---")
            print(form.errors)
            print("----------------------------------------\n")
    else:
        form = CustomerCreationForm()

    return render(request, 'customers/register.html', {'form': form})

def verify_email_view(request, uidb64, token):
    '''
    Validates the secure email verification link clicked by the user.
    If the cryptographic token is valid and not expired, activates the customer's account.

    Args:
        request (HttpRequest): The HTTP request object.
        uidb64 (str): The base64 encoded user ID.
        token (str): The cryptographic verification token.

    Returns:
        HttpResponseRedirect: Redirects to the login page with a success or error message.
    '''
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Customer.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Customer.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'E-mail confirmado com sucesso! Você já pode fazer login.')
        return redirect('customers:login')
    else:
        messages.error(request, 'O link de verificação é inválido ou expirou. Tente se cadastrar novamente.')
        return redirect('customers:register')
    
@login_required
def profile_view(request):
    '''
    Renders the user profile page.
    Retrieves all customer addresses, with the default address listed first.
    '''
    addresses = request.user.addresses.all().order_by('-is_default', '-created_at')
        
    return render(request, 'customers/profile.html', {'addresses': addresses})

@login_required
def profile_update_view(request):
    '''
    Handles the updating of user personal information.
    '''
    if request.method == 'POST':
        form = CustomerUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados pessoais atualizados com sucesso!')
            return redirect('customers:profile')
    else:
        form = CustomerUpdateForm(instance=request.user)
        
    return render(request, 'customers/profile_update.html', {'form': form})

@login_required
def address_update_view(request, pk):
    '''
    Handles the updating of an existing user address.
    Ensures the user can only edit their own addresses to maintain security.
    '''
    address = get_object_or_404(Address, pk=pk, customer=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Endereço atualizado com sucesso!')
            return redirect('customers:profile')
    else:
        form = AddressForm(instance=address)

    return render(request, 'customers/address_update.html', {'form': form})

def logout_view(request):
    '''
    Terminates the user's session and redirects them to the login page
    with a farewell message.
    '''
    logout(request)
    messages.success(request, "Sessão terminada com sucesso. Esperamos ver você novamente em breve!")
    return redirect('customers:login')

def help_center_view(request):
    '''
    Renders the static help center and FAQ page for customer support.
    '''
    return render(request, 'customers/help_center.html')