# Afterpay Integration Guide for Lavish Library

## Overview

This guide outlines the complete implementation of Afterpay as a payment option for subscription orders in the Lavish Library platform, with bidirectional integration between Django backend and Shopify store.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CUSTOMER CHECKOUT FLOW                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SHOPIFY STOREFRONT                            │
│  • Customer selects subscription product                         │
│  • Adds to cart                                                  │
│  • Proceeds to checkout                                          │
│  • Selects "Afterpay" as payment method                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                SHOPIFY CHECKOUT + PAYMENT GATEWAY                │
│  • Shopify communicates with Afterpay via installed app         │
│  • Creates Afterpay checkout session                            │
│  • Redirects customer to Afterpay portal                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AFTERPAY PAYMENT PORTAL                        │
│  • Customer authenticates with Afterpay                          │
│  • Reviews payment schedule (4 installments)                     │
│  • Approves payment                                              │
│  • Redirects back to merchant                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              DJANGO BACKEND (Lavish Library)                     │
│  • Receives webhook/notification from Shopify                    │
│  • Captures payment via Afterpay API                            │
│  • Creates subscription in Django                                │
│  • Syncs back to Shopify                                        │
│  • Sends confirmation email                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created

### 1. `/payments/afterpay_models.py` ✅
**Purpose**: Database models for Afterpay integration

**Models**:
- `AfterpayConfiguration`: Stores merchant credentials and settings
  - Merchant ID (username)
  - Secret Key (password)
  - Environment (sandbox/production)
  - Region (US, AU, NZ, CA, GB)
  - Payment limits (min/max amounts)
  - Active status and default flag

- `AfterpayCheckout`: Tracks checkout sessions
  - Afterpay token
  - Order ID
  - Amount and currency
  - Customer details
  - Status tracking
  - Links to Shopify orders and subscriptions

- `AfterpayPaymentEvent`: Individual payment events
  - AUTH_APPROVED, CAPTURED, REFUNDED, etc.
  - Event timestamps
  - Amount tracking

- `AfterpayRefund`: Refund tracking
  - Refund IDs
  - Amounts
  - Status
  - Idempotency keys

- `AfterpayWebhook`: Incoming webhook events
  - Event types
  - Payloads
  - Processing status

### 2. `/payments/afterpay_client.py` ✅
**Purpose**: Afterpay API client for all API interactions

**Key Methods**:
- `get_configuration()`: Fetch merchant payment limits
- `create_checkout()`: Create checkout session
- `auth_payment()`: Authorize payment (deferred flow)
- `capture_payment_full()`: Immediate capture
- `capture_payment_partial()`: Partial capture after auth
- `create_refund()`: Process refunds
- `void_payment()`: Cancel authorized payment
- `validate_amount()`: Check payment limits

**Features**:
- Basic authentication handling
- Proper timeout configuration (10s open, 20-70s read)
- Comprehensive error handling
- Logging for debugging
- Helper methods for data formatting

## Implementation Steps

### Phase 1: Django Admin Setup (Week 1)

#### Step 1.1: Add Models to Admin
Create `/payments/afterpay_admin.py`:

```python
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .afterpay_models import (
    AfterpayConfiguration,
    AfterpayCheckout,
    AfterpayPaymentEvent,
    AfterpayRefund,
    AfterpayWebhook
)
from .afterpay_client import AfterpayClient


@admin.register(AfterpayConfiguration)
class AfterpayConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'status_icon',
        'name',
        'environment_badge',
        'region',
        'payment_limits_display',
        'is_default',
        'config_status',
        'test_connection_button'
    ]
    list_filter = ['environment', 'region', 'is_active', 'is_default']
    search_fields = ['name', 'merchant_id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active', 'is_default')
        }),
        ('Environment & Region', {
            'fields': ('environment', 'region')
        }),
        ('API Credentials', {
            'fields': ('merchant_id', 'secret_key'),
            'description': 'Enter your Afterpay merchant credentials (username and password)'
        }),
        ('Payment Configuration', {
            'fields': ('currency', 'min_amount', 'max_amount', 'config_last_fetched'),
            'description': 'Payment limits are automatically fetched from Afterpay'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'config_last_fetched']
    
    actions = ['fetch_configuration', 'test_connection', 'set_as_default']
    
    def status_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    status_icon.short_description = 'Status'
    
    def environment_badge(self, obj):
        if obj.environment == 'production':
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 4px; font-weight: bold;">LIVE</span>'
            )
        return format_html(
            '<span style="background: #ffc107; color: black; padding: 3px 8px; '
            'border-radius: 4px; font-weight: bold;">TEST</span>'
        )
    environment_badge.short_description = 'Environment'
    
    def payment_limits_display(self, obj):
        if obj.min_amount and obj.max_amount:
            return format_html(
                '<span style="color: #4CAF50;">${} - ${}</span>',
                obj.min_amount,
                obj.max_amount
            )
        return format_html('<span style="color: #999;">Not fetched</span>')
    payment_limits_display.short_description = 'Payment Limits'
    
    def config_status(self, obj):
        if not obj.config_last_fetched:
            return format_html('<span style="color: #ff9800;">Never fetched</span>')
        
        age = timezone.now() - obj.config_last_fetched
        if age.days > 1:
            return format_html(
                '<span style="color: #ff5722;">Outdated ({} days)</span>',
                age.days
            )
        return format_html('<span style="color: #4CAF50;">Up to date</span>')
    config_status.short_description = 'Config Status'
    
    def test_connection_button(self, obj):
        if obj.pk:
            return format_html(
                '<a class="button" href="{}">Test Connection</a>',
                reverse('admin:afterpay_test_connection', args=[obj.pk])
            )
        return '-'
    test_connection_button.short_description = 'Actions'
    
    def fetch_configuration(self, request, queryset):
        """Fetch payment limits from Afterpay"""
        for config in queryset:
            try:
                client = AfterpayClient(
                    config.merchant_id,
                    config.secret_key,
                    config.environment,
                    config.region
                )
                
                result = client.get_configuration()
                
                if 'minimumAmount' in result:
                    config.min_amount = result['minimumAmount']['amount']
                if 'maximumAmount' in result:
                    config.max_amount = result['maximumAmount']['amount']
                
                config.config_last_fetched = timezone.now()
                config.save()
                
                self.message_user(
                    request,
                    f'Successfully fetched configuration for {config.name}'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Failed to fetch config for {config.name}: {str(e)}',
                    level='ERROR'
                )
    fetch_configuration.short_description = 'Fetch Payment Limits from Afterpay'


@admin.register(AfterpayCheckout)
class AfterpayCheckoutAdmin(admin.ModelAdmin):
    list_display = [
        'merchant_reference',
        'status_badge',
        'amount_display',
        'customer_email',
        'created_at',
        'expires_at',
        'is_expired_display',
        'view_details'
    ]
    list_filter = ['status', 'configuration', 'created_at']
    search_fields = [
        'merchant_reference',
        'afterpay_token',
        'afterpay_order_id',
        'customer_email'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Checkout Information', {
            'fields': (
                'afterpay_token',
                'afterpay_order_id',
                'configuration',
                'status',
                'payment_state'
            )
        }),
        ('Order Details', {
            'fields': (
                'merchant_reference',
                'amount',
                'currency',
                'redirect_checkout_url'
            )
        }),
        ('Customer Information', {
            'fields': (
                'customer_email',
                'customer_first_name',
                'customer_last_name',
                'customer_phone'
            )
        }),
        ('Integration', {
            'fields': (
                'shopify_order_id',
                'subscription_id'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'expires_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def status_badge(self, obj):
        colors = {
            'created': '#2196F3',
            'pending': '#ff9800',
            'approved': '#4CAF50',
            'declined': '#f44336',
            'expired': '#9e9e9e',
            'captured': '#4CAF50',
            'cancelled': '#f44336'
        }
        color = colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 4px; font-weight: 500;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def amount_display(self, obj):
        return format_html('${} {}', obj.amount, obj.currency)
    amount_display.short_description = 'Amount'
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        return format_html('<span style="color: green;">✓ Valid</span>')
    is_expired_display.short_description = 'Valid'
    
    def view_details(self, obj):
        return format_html(
            '<a class="button" href="{}">View Events</a>',
            reverse('admin:payments_afterpaypaymentevent_changelist') + f'?checkout__id__exact={obj.id}'
        )
    view_details.short_description = 'Actions'
```

#### Step 1.2: Update Admin Registration
In `/payments/admin.py`, add:

```python
# Import Afterpay admin
from .afterpay_admin import (
    AfterpayConfigurationAdmin,
    AfterpayCheckoutAdmin
)

# Register the models if not already registered in afterpay_admin.py
```

#### Step 1.3: Update Settings Icons
Add Afterpay icons to `/core/settings.py`:

```python
"icons": {
    # ... existing icons ...
    
    # Afterpay Integration
    "payments.afterpayconfiguration": "fas fa-cog",
    "payments.afterpaycheckout": "fas fa-shopping-cart",
    "payments.afterpaypaymentevent": "fas fa-history",
    "payments.afterpayrefund": "fas fa-undo",
    "payments.afterpaywebhook": "fas fa-plug",
}
```

### Phase 2: Database Migration

#### Step 2.1: Create Migration
```bash
cd app/lavish_backend
python manage.py makemigrations payments
python manage.py migrate
```

#### Step 2.2: Create Initial Configuration
In Django admin:
1. Navigate to **Payments > Afterpay Configurations**
2. Click **Add Afterpay Configuration**
3. Fill in:
   - **Name**: "Lavish Library Afterpay (Sandbox)"
   - **Environment**: Sandbox (Testing)
   - **Region**: US (or your region)
   - **Merchant ID**: Your Afterpay merchant ID
   - **Secret Key**: Your Afterpay secret key
   - **Currency**: USD
   - **Is Active**: ✓
   - **Is Default**: ✓
4. Click **Save**
5. Use the **"Fetch Payment Limits from Afterpay"** action to retrieve min/max amounts

### Phase 3: Shopify Integration

#### Step 3.1: Install Afterpay App in Shopify
1. Go to your Shopify admin
2. Navigate to **Apps**
3. Search for **"Afterpay"** in the Shopify App Store
4. Install the **Afterpay** app
5. Follow the setup wizard to connect your Afterpay merchant account

#### Step 3.2: Configure Afterpay in Shopify Payments
1. Go to **Settings > Payments**
2. Under **Alternative payment methods**, you should now see **Afterpay**
3. Click **Activate** or **Manage**
4. Configure:
   - Enable Afterpay for your store
   - Set regions/countries where available
   - Configure messaging display

#### Step 3.3: Enable Afterpay for Subscriptions
Create `/shopify_integration/afterpay_integration.py`:

```python
"""
Afterpay integration with Shopify
Handles bidirectional sync and payment processing
"""

from django.conf import settings
from payments.afterpay_client import AfterpayClient
from payments.afterpay_models import (
    AfterpayConfiguration,
    AfterpayCheckout,
    AfterpayPaymentEvent
)
from customer_subscriptions.models import CustomerSubscription
from orders.models import ShopifyOrder
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class ShopifyAfterpayBridge:
    """
    Bridges Shopify orders with Afterpay payments
    """
    
    def __init__(self, configuration=None):
        """Initialize with Afterpay configuration"""
        if configuration is None:
            configuration = AfterpayConfiguration.objects.filter(
                is_active=True,
                is_default=True
            ).first()
            
            if not configuration:
                raise ValueError("No active Afterpay configuration found")
        
        self.configuration = configuration
        self.client = AfterpayClient(
            merchant_id=configuration.merchant_id,
            secret_key=configuration.secret_key,
            environment=configuration.environment,
            region=configuration.region
        )
    
    def create_checkout_for_subscription(
        self,
        subscription,
        customer_email,
        amount,
        currency='USD'
    ):
        """
        Create Afterpay checkout for a subscription order
        
        Args:
            subscription: CustomerSubscription instance
            customer_email: Customer email
            amount: Total amount
            currency: Currency code
        
        Returns:
            AfterpayCheckout instance
        """
        logger.info(f"Creating Afterpay checkout for subscription {subscription.id}")
        
        # Validate amount
        validation = self.client.validate_amount(Decimal(amount), currency)
        if not validation['valid']:
            raise ValueError(validation['message'])
        
        # Create checkout via API
        result = self.client.create_checkout(
            amount=Decimal(amount),
            currency=currency,
            consumer_email=customer_email,
            merchant_reference=f"SUB-{subscription.id}"
        )
        
        # Save to database
        checkout = AfterpayCheckout.objects.create(
            afterpay_token=result['token'],
            configuration=self.configuration,
            merchant_reference=f"SUB-{subscription.id}",
            amount=amount,
            currency=currency,
            customer_email=customer_email,
            status='created',
            redirect_checkout_url=result['redirectCheckoutUrl'],
            expires_at=result['expires'],
            subscription_id=str(subscription.id)
        )
        
        logger.info(f"Afterpay checkout created: {checkout.id}")
        return checkout
    
    def process_shopify_order_webhook(self, order_data):
        """
        Process Shopify order webhook that includes Afterpay payment
        
        Args:
            order_data: Shopify order webhook payload
        """
        # Check if payment method is Afterpay
        payment_gateway = order_data.get('payment_gateway_names', [])
        
        if 'Afterpay' not in payment_gateway:
            logger.info("Order does not use Afterpay, skipping")
            return
        
        logger.info(f"Processing Afterpay order: {order_data['id']}")
        
        # Extract order details
        shopify_order_id = str(order_data['id'])
        order_number = order_data.get('order_number')
        total_price = Decimal(order_data['total_price'])
        currency = order_data['currency']
        customer_email = order_data['customer']['email']
        
        # Check if this is a subscription order
        line_items = order_data.get('line_items', [])
        subscription_items = [
            item for item in line_items
            if 'subscription' in item.get('properties', {})
        ]
        
        if not subscription_items:
            logger.info("No subscription items in order")
            return
        
        # Find or create Afterpay checkout
        merchant_ref = f"SHOPIFY-{order_number}"
        
        try:
            checkout = AfterpayCheckout.objects.get(
                merchant_reference=merchant_ref
            )
        except AfterpayCheckout.DoesNotExist:
            # Create checkout record (payment already processed by Shopify)
            checkout = AfterpayCheckout.objects.create(
                afterpay_token='',  # We don't have token from Shopify
                configuration=self.configuration,
                merchant_reference=merchant_ref,
                amount=total_price,
                currency=currency,
                customer_email=customer_email,
                status='captured',  # Already captured by Shopify
                shopify_order_id=shopify_order_id,
                redirect_checkout_url='',
                expires_at=timezone.now() + timedelta(days=1)
            )
        
        # Create subscription in Django
        self._create_subscription_from_order(order_data, checkout)
        
        logger.info(f"Afterpay order processed successfully: {checkout.id}")
    
    def _create_subscription_from_order(self, order_data, checkout):
        """Create Django subscription from Shopify order"""
        # Implementation depends on your subscription model structure
        # This is a placeholder showing the integration point
        pass
```

### Phase 4: Webhook Setup

#### Step 4.1: Create Webhook Endpoint
Create `/payments/views.py` (if not exists) and add:

```python
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
from .afterpay_models import AfterpayWebhook

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def afterpay_webhook(request):
    """
    Receive webhooks from Afterpay
    """
    try:
        payload = json.loads(request.body)
        
        # Save webhook
        webhook = AfterpayWebhook.objects.create(
            event_type=payload.get('eventType', 'unknown'),
            afterpay_order_id=payload.get('orderId', ''),
            merchant_reference=payload.get('merchantReference', ''),
            payload=payload,
            processed=False
        )
        
        logger.info(f"Afterpay webhook received: {webhook.id}")
        
        # Process webhook asynchronously (implement as needed)
        # process_afterpay_webhook.delay(webhook.id)
        
        return JsonResponse({'status': 'received'}, status=200)
    
    except Exception as e:
        logger.error(f"Error processing Afterpay webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def shopify_order_webhook(request):
    """
    Receive order webhooks from Shopify
    Detect Afterpay payments and process them
    """
    try:
        payload = json.loads(request.body)
        
        # Check for Afterpay payment
        from shopify_integration.afterpay_integration import ShopifyAfterpayBridge
        
        bridge = ShopifyAfterpayBridge()
        bridge.process_shopify_order_webhook(payload)
        
        return JsonResponse({'status': 'processed'}, status=200)
    
    except Exception as e:
        logger.error(f"Error processing Shopify order webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)
```

#### Step 4.2: Add URL Routes
In `/payments/urls.py` (create if needed):

```python
from django.urls import path
from . import views

urlpatterns = [
    path('webhooks/afterpay/', views.afterpay_webhook, name='afterpay_webhook'),
    path('webhooks/shopify/orders/', views.shopify_order_webhook, name='shopify_order_webhook'),
]
```

In main `/core/urls.py`, include:

```python
path('payments/', include('payments.urls')),
```

### Phase 5: Testing Workflow

#### Test Scenario 1: Direct Afterpay Checkout
1. In Django admin, create a test subscription
2. Navigate to **Afterpay Checkouts**
3. Create a new checkout with test data
4. Copy the `redirect_checkout_url`
5. Open URL in browser
6. Complete Afterpay flow in sandbox
7. Return to Django admin
8. Run **"Fetch Payment Status"** action
9. Verify status updated to "approved" or "captured"

#### Test Scenario 2: Shopify Store Integration
1. Configure Afterpay in Shopify (sandbox mode)
2. Create a subscription product in Shopify
3. Add product to cart on storefront
4. Proceed to checkout
5. Select **Afterpay** as payment method
6. Complete Afterpay authentication
7. Check Django admin:
   - Verify webhook received
   - Check AfterpayCheckout created
   - Verify subscription created
8. Check Shopify admin:
   - Verify order marked as paid
   - Check payment method shows Afterpay

## Best Practices

### Security
1. **Never expose credentials**: Use environment variables for production
2. **Use webhooks**: Don't rely solely on redirects
3. **Validate webhook signatures**: Implement HMAC verification
4. **Use HTTPS**: Always use SSL/TLS for API calls

### Error Handling
1. **Idempotency**: Use `request_id` for retries
2. **Logging**: Log all API calls and responses
3. **Graceful degradation**: Handle Afterpay downtime
4. **Customer communication**: Send clear error messages

### Performance
1. **Cache configuration**: Fetch payment limits once per day
2. **Async processing**: Use Celery for webhook processing
3. **Database indexing**: Index frequently queried fields
4. **Connection pooling**: Reuse HTTP connections

### Testing
1. **Use sandbox first**: Always test in sandbox environment
2. **Test all flows**: Auth-capture, immediate capture, refunds
3. **Test expiration**: Verify 13-day auth expiration handling
4. **Test edge cases**: Declined payments, network errors

## Deployment Checklist

### Pre-Production
- [ ] All models created and migrated
- [ ] Admin interface configured
- [ ] Sandbox configuration tested
- [ ] Webhook endpoints created
- [ ] Shopify app installed (sandbox)
- [ ] End-to-end test completed
- [ ] Error handling verified
- [ ] Logging configured

### Production
- [ ] Create production Afterpay configuration
- [ ] Update environment variables
- [ ] Configure production webhooks
- [ ] Install Afterpay in production Shopify
- [ ] Update Shopify webhook URLs
- [ ] Test with real (small) transaction
- [ ] Monitor logs for first 24 hours
- [ ] Set up alerting for failed payments

## Support Resources

### Afterpay Documentation
- API Reference: https://developers.afterpay.com/afterpay-online/reference
- Integration Guide: https://developers.afterpay.com/afterpay-online/docs
- Sandbox Environment: https://portal.sandbox.afterpay.com

### Shopify Resources
- Afterpay App: https://apps.shopify.com/afterpay
- Payment Gateway API: https://shopify.dev/api/admin-rest/2024-01/resources/payment
- Webhooks: https://shopify.dev/api/admin-rest/2024-01/resources/webhook

### Contact
- Afterpay Support: merchant.support@afterpay.com
- Shopify Partner Support: partners.shopify.com/support

## Troubleshooting

### Common Issues

**Issue**: "Amount exceeds maximum"
- **Solution**: Check merchant configuration limits via `get_configuration()`
- **Prevention**: Cache and validate limits before checkout creation

**Issue**: "Authorization expired"
- **Solution**: Authorizations expire after 13 days, must re-auth
- **Prevention**: Monitor auth expiration dates, auto-void before expiry

**Issue**: "Webhook not received"
- **Solution**: Check webhook URL configuration, firewall rules
- **Prevention**: Implement webhook retry logic, monitor webhook delivery

**Issue**: "Shopify not showing Afterpay"
- **Solution**: Verify Afterpay app activated, check region settings
- **Prevention**: Test in different browsers, check Shopify payment settings

## Next Steps

1. ✅ Review this guide
2. Run database migrations
3. Configure Afterpay in Django admin
4. Install Afterpay app in Shopify (sandbox)
5. Test checkout flow end-to-end
6. Review and adjust error handling
7. Set up monitoring and alerts
8. Plan production rollout

---

**Last Updated**: December 3, 2025
**Version**: 1.0
**Status**: Ready for Implementation
