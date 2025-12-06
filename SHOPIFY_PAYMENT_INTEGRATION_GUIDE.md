# Django Subscription App with Shopify Payment Integration

## Overview

This implementation allows your Django backend to create and manage subscriptions that utilize **Shopify's saved payment methods**, eliminating the need for Django to handle payment processing directly.

## Architecture

```
Customer → Django API → Shopify Payment Methods API → Shopify Subscriptions
                ↓
         Django Database (Sync)
```

### Key Benefits

1. **Payment Security**: Shopify handles all payment data - PCI compliance managed by Shopify
2. **Saved Payment Methods**: Leverage customer's existing payment methods stored in Shopify
3. **Automatic Billing**: Shopify processes recurring charges automatically
4. **Bidirectional Sync**: Subscriptions created in Django sync to Shopify and vice versa
5. **No Payment Processing**: Django never touches sensitive payment data

## How It Works

### 1. Customer Has Payment Method Saved in Shopify

When a customer makes a purchase through your Shopify store, their payment method is automatically saved by Shopify (if they opt-in).

### 2. Django Retrieves Available Payment Methods

```python
from customer_subscriptions.shopify_payment_service import ShopifyPaymentMethodService

# Get customer's saved payment methods
payment_service = ShopifyPaymentMethodService()
customer_data = payment_service.get_customer_payment_methods(customer_id)

# Payment methods include:
# - Credit/debit cards (with masked numbers)
# - PayPal billing agreements
# - Shop Pay
# - Other Shopify-supported methods
```

### 3. Django Creates Subscription Using Shopify Payment Method

```python
# Create subscription in Shopify using saved payment method
result = payment_service.create_subscription_contract_with_payment(
    customer_id="123456",
    payment_method_id="gid://shopify/CustomerPaymentMethod/abc123",
    selling_plan_details={
        'billing_interval': 'MONTH',
        'billing_interval_count': 1,
        'delivery_interval': 'MONTH',
        'delivery_interval_count': 1,
        'line_items': [
            {
                'variant_id': 'gid://shopify/ProductVariant/789',
                'quantity': 1,
                'price': '29.99'
            }
        ]
    }
)

# Result includes Shopify subscription contract ID
subscription_contract_id = result['contract']['id']
```

### 4. Shopify Handles All Billing

- Shopify automatically charges the saved payment method on billing dates
- Failed payments trigger Shopify's dunning process
- Successful payments create orders in Shopify
- Django receives webhook notifications about billing events

## API Endpoints

### Get Customer Payment Methods

```http
GET /api/customer-subscriptions/customers/{customer_id}/payment-methods/
Authorization: Bearer {token}
```

**Response:**
```json
{
    "customer": {
        "id": "gid://shopify/Customer/123456",
        "name": "John Doe",
        "email": "john@example.com"
    },
    "payment_methods": [
        {
            "id": "gid://shopify/CustomerPaymentMethod/abc123",
            "type": "CREDIT_CARD",
            "brand": "Visa",
            "last_digits": "4242",
            "expiry_month": 12,
            "expiry_year": 2025,
            "masked_number": "•••• 4242"
        }
    ]
}
```

### Create Subscription with Saved Payment

```http
POST /api/customer-subscriptions/create-with-payment/
Authorization: Bearer {token}
Content-Type: application/json

{
    "customer_id": "123456",
    "selling_plan_id": 1,
    "payment_method_id": "gid://shopify/CustomerPaymentMethod/abc123",
    "line_items": [
        {
            "variant_id": "gid://shopify/ProductVariant/789",
            "quantity": 1,
            "price": "29.99",
            "selling_plan_id": "gid://shopify/SellingPlan/456"
        }
    ],
    "delivery_address": {
        "address1": "123 Main St",
        "city": "New York",
        "province": "NY",
        "country": "US",
        "zip": "10001"
    }
}
```

**Response:**
```json
{
    "success": true,
    "subscription": {
        "id": 1,
        "shopify_id": "gid://shopify/SubscriptionContract/xyz789",
        "status": "ACTIVE",
        "next_billing_date": "2025-02-05",
        "total_price": "29.99"
    }
}
```

### Update Payment Method

```http
PUT /api/customer-subscriptions/{subscription_id}/payment-method/
Authorization: Bearer {token}
Content-Type: application/json

{
    "payment_method_id": "gid://shopify/CustomerPaymentMethod/new123"
}
```

## Database Models

### SellingPlan (Subscription Plan)

Already exists in your app - represents subscription plan configurations.

### CustomerSubscription

Already exists - enhanced with `payment_method_id` field:

```python
class CustomerSubscription(models.Model):
    # ... existing fields ...
    payment_method_id = models.CharField(max_length=255)  # Shopify payment method ID
    shopify_id = models.CharField(max_length=255)  # Subscription contract ID
```

## Webhook Integration

Set up these Shopify webhooks to stay synchronized:

### 1. Subscription Billing Success
```
Topic: subscription_billing_attempts/success
Endpoint: /api/webhooks/shopify/subscription-billing-success/
```

### 2. Subscription Billing Failure
```
Topic: subscription_billing_attempts/failure
Endpoint: /api/webhooks/shopify/subscription-billing-failure/
```

### 3. Subscription Contract Update
```
Topic: subscription_contracts/update
Endpoint: /api/webhooks/shopify/subscription-update/
```

## Required Shopify Scopes

Add these to your Shopify app:

```
read_customer_payment_methods
write_own_subscription_contracts
read_own_subscription_contracts
read_customers
write_products
```

## Implementation Steps

### 1. Update Requirements

```bash
pip install shopify-api-python
```

### 2. Configure Settings

```python
# settings.py
SHOPIFY_STORE_URL = 'your-store.myshopify.com'
SHOPIFY_ACCESS_TOKEN = 'your-access-token'
SHOPIFY_API_VERSION = '2024-10'
```

### 3. Include URLs

```python
# core/urls.py
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('api/customer-subscriptions/', include('customer_subscriptions.urls')),
]
```

### 4. Test the Integration

```python
# Test script
from customer_subscriptions.shopify_payment_service import ShopifyPaymentMethodService

service = ShopifyPaymentMethodService()

# Get customer payment methods
methods = service.get_customer_payment_methods('123456')
print(f"Found {len(methods['paymentMethods']['edges'])} payment methods")

# Create subscription
result = service.create_subscription_contract_with_payment(
    customer_id='123456',
    payment_method_id=methods['paymentMethods']['edges'][0]['node']['id'],
    selling_plan_details={...}
)
```

## Security Considerations

1. **No Payment Data Storage**: Django never stores card numbers or sensitive payment data
2. **Token-Based Auth**: All API endpoints require authentication
3. **Webhook Verification**: Verify Shopify webhook signatures
4. **HTTPS Required**: All communication over HTTPS
5. **Scope Limitations**: Request only necessary Shopify API scopes

## Advantages Over Django Payment Processing

| Feature | Shopify Payments | Django Payments |
|---------|-----------------|-----------------|
| PCI Compliance | Handled by Shopify | Your responsibility |
| Payment Methods | Customer's saved cards | Must collect & store |
| Failed Payment Retry | Automatic (Shopify) | Must implement |
| Multiple Payment Types | All Shopify types | Integrate each separately |
| International Payments | Shopify handles | Complex setup |
| Dunning Management | Built-in | Must build |
| 3D Secure | Handled by Shopify | Must implement |

## Example: Complete Subscription Flow

```python
from customer_subscriptions.shopify_payment_service import ShopifyPaymentMethodService
from customer_subscriptions.models import CustomerSubscription, SellingPlan
from customers.models import ShopifyCustomer

def create_monthly_subscription(customer_id, product_variant_id):
    """Complete example: Create a monthly subscription"""
    
    # 1. Get customer
    customer = ShopifyCustomer.objects.get(shopify_id=customer_id)
    
    # 2. Get or create selling plan
    selling_plan = SellingPlan.objects.get(
        name="Monthly Box",
        billing_interval="MONTH",
        billing_interval_count=1
    )
    
    # 3. Get customer's payment methods
    service = ShopifyPaymentMethodService()
    customer_data = service.get_customer_payment_methods(customer_id)
    
    payment_methods = customer_data['paymentMethods']['edges']
    if not payment_methods:
        return {"error": "No payment methods found"}
    
    # 4. Use first payment method
    payment_method_id = payment_methods[0]['node']['id']
    
    # 5. Create subscription in Shopify
    result = service.create_subscription_contract_with_payment(
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        selling_plan_details={
            'billing_interval': 'MONTH',
            'billing_interval_count': 1,
            'delivery_interval': 'MONTH',
            'delivery_interval_count': 1,
            'line_items': [{
                'variant_id': product_variant_id,
                'quantity': 1,
                'price': '29.99',
                'selling_plan_id': selling_plan.shopify_id
            }],
            'currency': 'USD'
        }
    )
    
    if not result['success']:
        return {"error": result['errors']}
    
    # 6. Save to Django database
    subscription = CustomerSubscription.objects.create(
        customer=customer,
        selling_plan=selling_plan,
        shopify_id=result['contract']['id'],
        payment_method_id=payment_method_id,
        status='ACTIVE',
        line_items=[{
            'variant_id': product_variant_id,
            'quantity': 1,
            'price': '29.99'
        }],
        total_price=29.99
    )
    
    return {
        "success": True,
        "subscription_id": subscription.id,
        "shopify_contract_id": subscription.shopify_id
    }
```

## Conclusion

This implementation allows you to:
- ✅ Create subscriptions using Shopify's saved payment methods
- ✅ Let Shopify handle all payment processing and PCI compliance
- ✅ Maintain subscription data in Django for business logic
- ✅ Sync bidirectionally between Django and Shopify
- ✅ Provide a seamless customer experience

The Django app acts as the "brains" for subscription management, while Shopify acts as the "payment processor" - best of both worlds!
