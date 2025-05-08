from django.contrib import admin
from .models import CustomerAccount, Transaction

admin.site.register(CustomerAccount)
admin.site.register(Transaction)