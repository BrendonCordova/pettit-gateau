from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .forms import CustomerCreationForm, AddressForm
from django.contrib.auth.decorators import login_required

@login_required
def address_create_view(request):
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
    template_name = 'customers/login.html'
    redirect_authenticated_user = True

def register_view(request):
    if request.method == 'POST':
        form = CustomerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('orders:checkout')
        else:
            print("\n--- ERROS DE VALIDAÇÃO DO FORMULÁRIO ---")
            print(form.errors)
            print("----------------------------------------\n")
    else:
        form = CustomerCreationForm()

    return render(request, 'customers/register.html', {'form': form})