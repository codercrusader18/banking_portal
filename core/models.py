from django.db import models
from django.contrib.auth.models import User

class CustomerAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) #Temporary
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=10, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    contact = models.CharField(max_length=15, default='N/A')

    ACCOUNT_TYPES = [
        ('Savings', 'Savings'),
        ('Current', 'Current'),
    ]

    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='Savings')

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

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount} ({self.timestamp})"
