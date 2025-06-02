# core/forms/transfer_forms.py
from django import forms
from core.models import CustomerAccount

class TransferForm(forms.Form):
    from_account = forms.ModelChoiceField(
        queryset=CustomerAccount.objects.none(),
        label="From Account"
    )
    to_account_number = forms.CharField(
        max_length=10,
        label="To Account Number"
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01
    )
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_account'].queryset = CustomerAccount.objects.filter(user=user)