"""
Customer Subscriptions URL Configuration
Includes payment method integration endpoints and public API for Shopify theme
"""

from django.urls import path
from . import api_views

app_name = 'customer_subscriptions'

urlpatterns = [
    # Public API for Shopify Theme (no authentication required)
    path(
        'selling-plans/',
        api_views.get_selling_plans,
        name='selling-plans'
    ),
    path(
        'checkout/create/',
        api_views.create_subscription_checkout,
        name='checkout-create'
    ),
]

# Payment Method Management URLs (lazy imported to avoid shopify dependency issues)
# These require shopify-python-api package to be installed
try:
    from . import payment_views
    
    urlpatterns += [
        path(
            'customers/<str:customer_id>/payment-methods/',
            payment_views.get_customer_payment_methods,
            name='customer-payment-methods'
        ),
        path(
            'create-with-payment/',
            payment_views.create_subscription_with_saved_payment,
            name='create-with-payment'
        ),
        path(
            '<int:subscription_id>/payment-method/',
            payment_views.update_subscription_payment_method,
            name='update-payment-method'
        ),
        path(
            'verify-payment-method/',
            payment_views.verify_payment_method,
            name='verify-payment-method'
        ),
    ]
except ImportError:
    # Shopify payment views not available (shopify-python-api not installed)
    pass
