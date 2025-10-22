from django import forms
from rating.models import ProductReview
from django.utils.html import strip_tags

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'review': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def clean_review(self):
        review = self.cleaned_data["review"]
        return strip_tags(review)