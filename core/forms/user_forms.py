from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms

from core.models import LoanRequest, CustomerProfile

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    account_holder = forms.CharField(max_length=100, label="Full Name")
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)
    kyc_document = forms.FileField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # Base auth fields

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits")
        return phone

    def clean_kyc_document(self):
        document = self.cleaned_data['kyc_document']
        if document.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError("File too large (max 5MB)")
        return document

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False  # User can't login until approved
        user.is_approved = False

        if commit:
            user.save()
            # Create the customer profile with additional fields
            CustomerProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['account_holder'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                kyc_document=self.cleaned_data['kyc_document']
            )
        return user


class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = LoanRequest
        fields = ['account', 'loan_type', 'amount', 'duration_months', 'purpose']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'loan_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }