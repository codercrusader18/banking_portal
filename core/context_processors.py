from .models import User, AccountRequest

def admin_approvals(request):
    if request.user.is_staff:
        from .models import User, AccountRequest
        return {
            'pending_users': User.objects.filter(is_approved=False).count(),
            'pending_accounts': AccountRequest.objects.filter(is_approved=False).count()
        }
    return {}