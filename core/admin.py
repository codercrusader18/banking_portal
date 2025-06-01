from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings  # Needed for email settings
from .models import CustomerAccount, Transaction, CustomerProfile, AccountRequest

User = get_user_model()  # Get the currently active user model

class ProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    # fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_approved', 'is_staff')
    list_filter = ('is_approved', 'is_staff', 'is_superuser')
    actions = ['approve_users']

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True, is_active=True)
        for user in queryset:
            try:
                send_mail(
                    'Your Account Has Been Approved',
                    f'Hello {user.username},\n\nYour banking account has been approved. You can now log in at {settings.SITE_URL}',
                    settings.DEFAULT_FROM_EMAIL,  # From email address
                    [user.email],  # To email
                    fail_silently=False,
                )
            except Exception as e:
                self.message_user(request, f"Failed to send email to {user.email}: {str(e)}", level='ERROR')

        self.message_user(request, f"Successfully approved {updated} user(s)")

    approve_users.short_description = "Approve selected users"


class AccountRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_type', 'is_approved', 'requested_at', 'status')
    list_filter = ('is_approved', 'account_type')
    actions = ['approve_requests']
    readonly_fields = ('requested_at',)

    def status(self, obj):
        return "Approved" if obj.is_approved else "Pending"

    status.short_description = 'Status'
    status.admin_order_field = 'is_approved'

    def approve_requests(self, request, queryset):
        approved = 0
        for req in queryset:
            if not req.is_approved:  # Only process unapproved requests
                CustomerAccount.objects.create(
                    user=req.user,
                    profile=req.user.customerprofile,  # Ensure profile is linked
                    account_type=req.account_type,
                    name=f"{req.user.username}'s {req.account_type} Account"
                )
                approved += 1
        queryset.update(is_approved=True)
        self.message_user(request, f"Approved {approved} account request(s)")

    approve_requests.short_description = "Approve selected account requests"

if not admin.site.is_registered(User):
    admin.site.register(User, CustomUserAdmin)

# Register other models
admin.site.register(CustomerAccount)
admin.site.register(Transaction)
admin.site.register(AccountRequest, AccountRequestAdmin)