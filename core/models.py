from django.db import models

class CustomerAccount(models.Model):
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

