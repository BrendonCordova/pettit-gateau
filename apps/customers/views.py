from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .forms import CustomerCreationForm, AddressForm
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
    Overrides the default Django template and automatically redirects authenticated users.
    '''
    template_name = 'customers/login.html'
    redirect_authenticated_user = True

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
            # message = f'Olá, {user.first_name}!\n\nPor favor, clique no link abaixo para ativar sua conta:\n\n{verification_link} \
            #     \n\nCaso tenha alguma dúvida ou questionamento, entre em contato com nosso suport dev.gcbrendon@gmail.com \
            #     \n\nPettit Gateau'
            
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
    Fetches the user's default address (or the first available one) to display 
    on the profile dashboard.
    '''
    address = request.user.addresses.filter(is_default=True).first()
    if not address:
        address = request.user.addresses.first()
        
    return render(request, 'customers/profile.html', {'address': address})