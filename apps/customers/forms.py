from django.contrib.auth.forms import UserCreationForm
from .models import Customer, Address
from django import forms

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'name', 'zip_code', 'street', 'number', 'neighborhood',
            'city', 'state', 'complement', 'is_default'
        ]

        widgets = {
            field: forms.TextInput(attrs={'class': 'form-control'})
            for field in ['name', 'zip_code', 'street', 'number', 'neighborhood', 'city', 'state', 'complement']
        }

class CustomerCreationForm(UserCreationForm):
    class Meta:
        model = Customer
        fields = ('email', 'first_name', 'last_name', 'tax_id', 'phone')