from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from .models import CustomerAccount, Transaction, CustomerProfile
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.contrib.auth import login
from django.core.paginator import Paginator
import random

@login_required
def account_list(request):
    query = request.GET.get('q')
    accounts = CustomerAccount.objects.filter(user=request.user) #it is a base query set which ensures only the current logged in user's accounts are taken in account
    if query:
        accounts = accounts.objects.filter(
            Q(name__icontains=query) | Q(account_number__icontains=query)
        )

    total_balance = accounts.aggregate(Sum('balance'))['balance__sum'] or 0

    paginator = Paginator(accounts, 10)  # Show 10 accounts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/account_list.html',
                  {'accounts': accounts,
                   'query': query,
                   'total_balance': total_balance,
                   'page_obj' : page_obj
                   })

@login_required()
def account_detail(request, pk):
    account = get_object_or_404(CustomerAccount, pk=pk)
    return render(request, 'core/account_detail.html', {'account': account})

# core/views.py

@login_required
def create_account(request):
    if request.method == 'POST':
        account_type = request.POST.get('account_type')

        # Generate a unique account number
        prefix = 'SAV' if account_type == 'Savings' else 'CUR'
        last_account = CustomerAccount.objects.filter(
             account_number__startswith=prefix
        ).order_by('-account_number').first()
        last_num = int(last_account.account_number[3:]) if last_account else 0
        account_number = f"{prefix}{last_num + 1:04d}"  # SAV0001, SAV0002, etc.

        # Create the account
        CustomerAccount.objects.create(
            user=request.user,
            name=f"{request.user.username}",
            account_number=account_number,
            account_type=account_type,
            balance=0  # Start with 0 balance
        )
        messages.success(request, f"New {account_type} account created successfully!")
        return redirect('bank:account_list')

    return render(request, 'core/create_account.html')

def deposit(request, pk):
    account = get_object_or_404(CustomerAccount, pk=pk)
    if request.method == 'POST':
        try :
            amount = Decimal(request.POST.get('amount', 0))

            #VAlidate amount
            if amount <= Decimal(0):
                messages.error(request, "Amount must be greater than 0")
            else:
                account.balance += amount
                account.save()
                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    transaction_type='DEPOSIT',
                    description=f"Deposit of ₹{amount}"
                )
                messages.success(request, f"Deposited ₹{amount} successfully!")
                return redirect('bank:account_detail', pk=pk)

        except (InvalidOperation, TypeError):
            messages.error(request, "Please enter a valid number")
    return render(request, 'core/transaction_form.html', {'account': account, 'action': 'Deposit'})

def withdraw(request, pk):
    account = get_object_or_404(CustomerAccount, pk=pk)
    if request.method == 'POST':
        try :
            amount = Decimal(request.POST.get('amount', 0))

            #Validate amount
            if amount <= Decimal('0'):
                messages.error(request, "Invalid amount!")
            elif amount > account.balance:
                messages.error(request, "Insufficient funds!")
            else:
                account.balance -= amount
                account.save()
                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    transaction_type='WITHDRAW',
                    description=f"Withdrawal of ₹{amount}"
                )
                messages.success(request, f"Withdrew ₹{amount} successfully!")
                return redirect('bank:account_detail', pk=pk)
        except (InvalidOperation, TypeError):
            messages.error(request, "Invalid amount entered")
    return render(request, 'core/transaction_form.html', {'account': account, 'action': 'Withdraw'})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create customer profile
            profile = CustomerProfile.objects.create(
                user=user,
                full_name=request.POST.get('account_holder', user.username),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                kyc_verified=False
            )

            # Create bank account
            CustomerAccount.objects.create(
                user=user,
                profile=profile,
                name=f"{profile.full_name}'s Primary Account",
                # account_number=str(random.randint(100000, 999999)), this line has been removed because now account number will be generated a/c to a set of rules
                #on removing the above line the account_number is sent empty .create() will itself generate a/c number
                balance=0,
                account_type='Savings'
            )
            login(request, user)
            return redirect('bank:account_list')
    else :
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form, 'profile_fields': True }) # Add this to template context