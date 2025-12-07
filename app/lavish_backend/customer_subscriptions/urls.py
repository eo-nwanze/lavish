"""
Customer Subscriptions URL Configuration
Includes payment method integration endpoints, webhooks, and public API for Shopify theme
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

# Shopify Webhooks (imported conditionally)
try:
    from . import webhooks
    
    urlpatterns += [
        # Subscription Contract Webhooks
        path(
            'webhooks/subscription-contracts/create/',
            webhooks.subscription_contract_create_webhook,
            name='webhook-subscription-create'
        ),
        path(
            'webhooks/subscription-contracts/update/',
            webhooks.subscription_contract_update_webhook,
            name='webhook-subscription-update'
        ),
        
        # Billing Attempt Webhooks
        path(
            'webhooks/subscription-billing-attempts/success/',
            webhooks.subscription_billing_attempt_success_webhook,
            name='webhook-billing-success'
        ),
        path(
            'webhooks/subscription-billing-attempts/failure/',
            webhooks.subscription_billing_attempt_failure_webhook,
            name='webhook-billing-failure'
        ),
        
        # Payment Method Webhooks
        path(
            'webhooks/customer-payment-methods/create/',
            webhooks.customer_payment_method_create_webhook,
            name='webhook-payment-create'
        ),
        path(
            'webhooks/customer-payment-methods/revoke/',
            webhooks.customer_payment_method_revoke_webhook,
            name='webhook-payment-revoke'
        ),
    ]
except ImportError:
    pass

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
