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
]
