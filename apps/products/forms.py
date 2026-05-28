from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    '''
    Form for handling the creation and validation of customer product reviews.
    Customizes widget attributes for Bootstrap styling on the frontend.
    '''
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1,6)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'O que achou do perfume?'}),
        }