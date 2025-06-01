from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    account_holder = forms.CharField(max_length=100, label="Full Name")
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)
    kyc_document = forms.FileField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # Base auth fields

    def save(self, commit=True):
        user = super().save(commit=False)
        # Add custom fields to user model if needed
        if commit:
            user.save()
        return user