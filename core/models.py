from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import uuid


class CustomerProfile(models.Model):
    """Extended user profile containing CIF and other customer details"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cif_number = models.CharField(max_length=10, unique=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    kyc_verified = models.BooleanField(default=False)
    kyc_document = models.FileField(upload_to='kyc_documents/', null=True, blank=True)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) #Temporary
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
        ('TRANSFER_OUT', 'Transfer Out'),
        ('TRANSFER_IN', 'Transfer In'),
    ]

    account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=12, choices=TRANSACTION_TYPES)
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


class User(AbstractUser):
    is_approved = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    kyc_documents = models.FileField(upload_to='kyc/', null=True, blank=True)
    # Fix reverse accessor clashes
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",  # Changed
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",  # Changed
        related_query_name="user",
    )

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.username


class AccountRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=10, choices=CustomerAccount.ACCOUNT_TYPES)
    purpose = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.account_type} Account Request"


class LoanRequest(models.Model):
    LOAN_TYPES = [
        ('PERSONAL', 'Personal Loan'),
        ('HOME', 'Home Loan'),
        ('CAR', 'Car Loan'),
        ('EDUCATION', 'Education Loan'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # Default 10% interest
    purpose = models.TextField()
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def monthly_installment(self):
        # Calculate EMI using standard formula
        monthly_rate = self.interest_rate / 100 / 12
        return (self.amount * monthly_rate * (1 + monthly_rate) ** self.duration_months) / \
            ((1 + monthly_rate) ** self.duration_months - 1)

    def total_repayment(self):
        return self.monthly_installment() * self.duration_months

    def __str__(self):
        return f"{self.user.username} - {self.loan_type} Loan ({self.amount})"