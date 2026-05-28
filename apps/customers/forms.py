from django.contrib.auth.forms import UserCreationForm
from .models import Customer, Address
from django import forms

class AddressForm(forms.ModelForm):
    '''
    Form for handling the creation and validation of customer addresses.
    Customizes widget attributes for Bootstrap integration.
    '''
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
    '''
    Form for registering new customers. 
    Extends Django's default UserCreationForm to include custom fields 
    like first name, last name, tax ID, and phone.
    '''
    class Meta:
        model = Customer
        fields = ('email', 'first_name', 'last_name', 'tax_id', 'phone')