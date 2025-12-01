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
    path('subscriptions/<str:subscription_id>/renewal-info/', views.subscription_renewal_info, name='subscription_renewal_info'),
    path('subscriptions/<str:subscription_id>/skips/', views.subscription_skips_list, name='subscription_skips_list'),
    path('subscriptions/<str:subscription_id>/skip-quota/', views.skip_quota, name='skip_quota'),
    
    # Customer management operations
    path('subscriptions/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscriptions/pause/', views.pause_subscription, name='pause_subscription'),
    path('subscriptions/resume/', views.resume_subscription, name='resume_subscription'),
    path('subscriptions/change-frequency/', views.change_subscription_frequency, name='change_subscription_frequency'),
    path('subscriptions/<str:subscription_id>/options/', views.subscription_management_options, name='subscription_management_options'),
]
