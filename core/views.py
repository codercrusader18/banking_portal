import os

from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .forms.user_forms import CustomUserCreationForm, LoanRequestForm
from .models import CustomerAccount, Transaction, CustomerProfile, AccountRequest, LoanRequest
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.contrib.auth import login, get_user_model
from django.core.paginator import Paginator
from django.utils import timezone
import random

@login_required
def account_list(request):
    query = request.GET.get('q')
    accounts = CustomerAccount.objects.filter(user=request.user) #it is a base query set which ensures only the current logged in user's accounts are taken in account

    # Pending account requests
    pending_requests = AccountRequest.objects.filter(user=request.user, is_approved=False)

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
                   'pending_requests': pending_requests,
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
    if not request.user.is_approved:
        return HttpResponseForbidden("Your account needs admin approval")

    if request.method == 'POST':
        account_type = request.POST.get('account_type')

        # # Generate a unique account number
        # prefix = 'SAV' if account_type == 'Savings' else 'CUR'
        # last_account = CustomerAccount.objects.filter(
        #      account_number__startswith=prefix
        # ).order_by('-account_number').first()
        # last_num = int(last_account.account_number[3:]) if last_account else 0
        # account_number = f"{prefix}{last_num + 1:04d}"  # SAV0001, SAV0002, etc.

        purpose = request.POST.get('purpose', '')

        # Create the account
        AccountRequest.objects.create(
            user=request.user,
            account_type=account_type,
            purpose=purpose,
            is_approved=False
        )
        messages.success(request, 'Account request submitted for approval')
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
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.is_active = False  # User can't login until approved
            user.is_approved = False
            user.save()

            # Create customer profile
            profile = CustomerProfile.objects.create(
                user=user,
                full_name=request.POST.get('account_holder', user.username),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                kyc_verified=False,
                kyc_document = request.FILES.get('kyc_document')
            )

            messages.success(request, 'Registration submitted for admin approval')
            return redirect('bank:registration_submitted')
    else :
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form}) # Add this to template context


def registration_submitted(request):
    return render(request, 'registration/submitted.html', {
        'title': 'Application Submitted',
        'message': 'Your registration is pending admin approval'
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return HttpResponseForbidden("You don't have admin privileges")

    User = get_user_model()
    pending_users = User.objects.filter(is_approved=False)
    pending_accounts = AccountRequest.objects.filter(is_approved=False)
    pending_loans = LoanRequest.objects.filter(is_approved=False, is_rejected=False)

    return render(request, 'core/admin_dashboard.html', {
        'pending_users': pending_users,
        'pending_accounts': pending_accounts,
        'pending_loans': pending_loans,

    })


@login_required
def approve_user(request, user_id):
    if not request.user.is_admin:
        return HttpResponseForbidden("Admin access required")

    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()

    # Send approval email
    send_mail(
        'Account Approved',
        'Your account has been approved.',
        'admin@yourbank.com',
        [user.email]
    )

    messages.success(request, f"User {user.username} approved successfully")
    return redirect('admin_dashboard')


@login_required
def user_details(request, user_id):
    if not request.user.is_admin:
        return HttpResponseForbidden("Admin access required")

    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(CustomerProfile, user=user)
    accounts = CustomerAccount.objects.filter(user=user)
    transactions = Transaction.objects.filter(account__user=user)

    # Debug output
    print(f"KYC Document path: {profile.kyc_document.path if profile.kyc_document else 'None'}")
    print(f"File exists: {os.path.exists(profile.kyc_document.path) if profile.kyc_document else False}")

    return render(request, 'core/user_details.html', {
        'user': user,
        'profile': profile,
        'accounts': accounts,
        'transactions': transactions
    })

class CustomLoginView(LoginView):
    def get_success_url(self):
        if self.request.user.is_admin:
            return reverse('admin_dashboard')
        return reverse('bank:account_list')


@login_required
def reject_user(request, user_id):
    if not request.user.is_admin:
        return HttpResponseForbidden("Admin access required")

    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    # Optional: Send rejection email
    send_mail(
        'Account Rejected',
        'Your account registration has been rejected.',
        'admin@yourbank.com',
        [user.email]
    )

    # Delete the user or mark as rejected
    user.delete()  # or user.is_active = False; user.save()

    messages.success(request, f"User {user.username} rejected")
    return redirect('admin_dashboard')


@login_required
def approve_account(request, request_id):
    if not request.user.is_admin:
        return HttpResponseForbidden("Admin access required")

    account_request = get_object_or_404(AccountRequest, id=request_id)

    # Generate account number
    prefix = 'SAV' if account_request.account_type == 'Savings' else 'CUR'
    last_account = CustomerAccount.objects.filter(
        account_number__startswith=prefix
    ).order_by('-account_number').first()
    last_num = int(last_account.account_number[3:]) if last_account else 0
    account_number = f"{prefix}{last_num + 1:04d}"

    # Create the actual account
    CustomerAccount.objects.create(
        user=account_request.user,
        profile=account_request.user.customerprofile,
        name=f"{account_request.user.username}'s {account_request.account_type} Account",
        account_number=account_number,
        account_type=account_request.account_type,
        balance=0
    )

    # Mark request as approved
    account_request.is_approved = True
    account_request.save()

    # send_mail(
    #     'Account Approved',
    #     f'Your {account_request.account_type} account has been approved.',
    #     settings.DEFAULT_FROM_EMAIL,
    #     [account_request.user.email]
    # )

    user=get_user_model()
    print(f"Account approved for {user.username} - email would be sent here")
    messages.success(request, 'Account request approved')
    return redirect('admin_dashboard')


@login_required
def reject_account(request, request_id):
    if not request.user.is_admin:
        return HttpResponseForbidden("Admin access required")

    account_request = get_object_or_404(AccountRequest, id=request_id)
    account_request.delete()  # Or mark as rejected if you want to keep records

    messages.success(request, 'Account request rejected')
    return redirect('admin_dashboard')


@login_required
def cancel_request(request, request_id): #to cancel new account creation request
    account_request = get_object_or_404(AccountRequest, id=request_id, user=request.user)

    if request.method == 'POST':
        account_request.delete()
        messages.success(request, 'Account request cancelled successfully')

    return redirect('bank:account_list')


@login_required
def request_loan(request):
    account_id = request.GET.get('account')
    initial = {}

    if account_id:
        account = get_object_or_404(CustomerAccount, id=account_id, user=request.user)
        initial['account'] = account

    if request.method == 'POST':
        form = LoanRequestForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.interest_rate = 10.0  # Default rate, can be customized
            loan.save()
            messages.success(request, 'Loan request submitted for approval')
            return redirect('bank:loan_status')
    else:
        form = LoanRequestForm()
        # Only show accounts belonging to the current user
        form.fields['account'].queryset = CustomerAccount.objects.filter(user=request.user)

    return render(request, 'core/request_loan.html', {'form': form})


@login_required
def loan_status(request):
    loans = LoanRequest.objects.filter(user=request.user).order_by('-requested_at')
    return render(request, 'core/loan_status.html', {'loans': loans})


@login_required
@user_passes_test(lambda u: u.is_admin)
def approve_loan(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == 'POST':
        loan.is_approved = True
        loan.approved_at = timezone.now()
        loan.save()

        # Credit the loan amount to the account
        account = loan.account
        account.balance += loan.amount
        account.save()

        # Create a transaction record
        Transaction.objects.create(
            account=account,
            amount=loan.amount,
            transaction_type='LOAN',
            description=f"{loan.get_loan_type_display()} Loan Approved"
        )

        messages.success(request, 'Loan approved and amount credited')
        return redirect('admin_dashboard')

    context = {
        'loan': loan,
        'monthly_installment': loan.monthly_installment(),
        'total_repayment': loan.total_repayment(),
    }
    return render(request, 'core/approve_loan.html', context)


@login_required
@user_passes_test(lambda u: u.is_admin)
def reject_loan(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == 'POST':
        loan.is_rejected = True
        loan.save()
        messages.success(request, 'Loan request rejected')
        return redirect('admin_dashboard')

    return render(request, 'core/reject_loan.html', {'loan': loan})