from django.shortcuts import render
from .models import CustomerAccount
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import get_object_or_404

def account_list(request):
    query = request.GET.get('q')
    if query:
        accounts = CustomerAccount.objects.filter(
            Q(name__icontains=query) | Q(account_number__icontains=query)
        )
    else:
        accounts = CustomerAccount.objects.all()

    total_balance = accounts.aggregate(Sum('balance'))['balance__sum'] or 0

    return render(request, 'core/account_list.html', {'accounts': accounts, 'query': query, 'total_balance': total_balance})

def account_detail(request, pk):
    account = get_object_or_404(CustomerAccount, pk=pk)
    return render(request, 'core/account_detail.html', {'account': account})
