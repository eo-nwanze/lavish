"""
URL Configuration for Subscription Skips API
"""

from django.urls import path
from . import views

app_name = 'skips'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Skip operations
    path('skip/', views.skip_next_payment, name='skip_next_payment'),
    path('skip/<int:skip_id>/cancel/', views.cancel_skip, name='cancel_skip'),
    
    # Subscription details
    path('subscriptions/', views.customer_subscriptions, name='customer_subscriptions'),
    path('subscriptions/<str:subscription_id>/', views.subscription_details, name='subscription_details'),
    path('subscriptions/<str:subscription_id>/skips/', views.subscription_skips_list, name='subscription_skips_list'),
    path('subscriptions/<str:subscription_id>/skip-quota/', views.skip_quota, name='skip_quota'),
]
