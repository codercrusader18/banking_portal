"""
URL configuration for banking_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from core import views #Import your views
from core.views import CustomLoginView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication URLs (login/logout)
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('bank/', include('core.urls', namespace='bank')),  # Your existing bank URLs

    path('', RedirectView.as_view(url='/bank/accounts/', permanent=True)),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('approve-account/<int:request_id>/', views.approve_account, name='approve_account'),
    path('user-details/<int:user_id>/', views.user_details, name='user_details'),
    path('account-transactions/<int:account_id>/', views.account_transactions, name='account_transactions'),
    path('reject-user/<int:user_id>/', views.reject_user, name='reject_user'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
