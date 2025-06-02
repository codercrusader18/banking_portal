from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'bank'

urlpatterns = [
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.create_account, name='create_account'),
    path('accounts/<int:pk>/', views.account_detail, name='account_detail'),
    path('accounts/<int:pk>/deposit/', views.deposit, name='deposit'),
    path('accounts/<int:pk>/withdraw/', views.withdraw, name='withdraw'),
    path('register/', views.register, name='register'),
    path('accounts/request/', views.create_account, name='request_account'),
    path('registration-submitted/', views.registration_submitted, name='registration_submitted'),
    path('loans/request/', views.request_loan, name='request_loan'),
    path('loans/status/', views.loan_status, name='loan_status'),
    path('loans/approve/<int:loan_id>/', views.approve_loan, name='approve_loan'),
    path('loans/reject/<int:loan_id>/', views.reject_loan, name='reject_loan'),
    path('loans/request/', views.request_loan, name='request_loan'),
    path('loans/status/', views.loan_status, name='loan_status'),
    path('transfer/', views.transfer_money, name='transfer'),
    path('cancel-request/<int:request_id>/', views.cancel_request, name='cancel_request'),
    path('api/validate-account/<str:account_number>/', views.validate_account),
]
