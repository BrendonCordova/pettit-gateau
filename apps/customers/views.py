from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .forms import CustomerCreationForm

class CustomerLoginView(LoginView):
    template_name = 'customers/login.html'
    redirect_authenticated_user = True

def register_view(request):
    if request.method == 'POST':
        form = CustomerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('carts:cart-page')
        else:
            print("\n--- ERROS DE VALIDAÇÃO DO FORMULÁRIO ---")
            print(form.errors)
            print("----------------------------------------\n")
    else:
        form = CustomerCreationForm()

    return render(request, 'customers/register.html', {'form': form})