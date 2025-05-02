from django.urls import path
from . import views

urlpatterns = [
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/<int:pk>/', views.account_detail, name='account_detail'),

]
