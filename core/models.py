from django.db import models
from django.contrib.auth.models import User
import uuid


class CustomerProfile(models.Model):
    """Extended user profile containing CIF and other customer details"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cif_number = models.CharField(max_length=10, unique=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    kyc_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.cif_number:
            # Generate CIF in format CIF000001
            last_profile = CustomerProfile.objects.order_by('-id').first()
            last_id = last_profile.id if last_profile else 0
            self.cif_number = f"CIF{(last_id + 1):06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cif_number} - {self.full_name}"



class CustomerAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) #Temporary
    profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=10, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    contact = models.CharField(max_length=15, default='N/A')

    ACCOUNT_TYPES = [
        ('Savings', 'Savings'),
        ('Current', 'Current'),
    ]

    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='Savings')

    def save(self, *args, **kwargs):
        # Auto-link to user's profile
        if not self.profile and hasattr(self.user, 'customerprofile'):
            self.profile = self.user.customerprofile

        # Generate only if not set
        if not self.account_number:
            prefix = 'SAV' if self.account_type == 'Savings' else 'CUR'
            last_account = CustomerAccount.objects.filter(
                account_number__startswith=prefix
            ).order_by('-account_number').first()
            last_num = int(last_account.account_number[3:]) if last_account else 0
            self.account_number = f"{prefix}{last_num + 1:04d}"  # SAV0001, SAV0002, etc.
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.account_number})"


# core/models.py
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('TRANSFER', 'Transfer'),
    ]

    account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)  # e.g., "Transfer to account X"
    related_account = models.ForeignKey(
        CustomerAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_transactions'
    )

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount} ({self.timestamp})"
