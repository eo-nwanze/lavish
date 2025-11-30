# Subscription Skip API - Quick Reference

## Base URL
```
http://localhost:8003/api/skips/
```

---

## 1. Skip Next Payment

**Endpoint:** `POST /api/skips/skip/`

**Request:**
```json
{
  "subscription_id": "gid://shopify/SubscriptionContract/123",
  "reason": "Going on vacation",
  "reason_details": "Will be away for 2 weeks"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Your payment has been successfully skipped",
  "skip": {
    "id": 1,
    "original_date": "2025-02-15",
    "new_date": "2025-03-15",
    "status": "confirmed",
    "fee_charged": "0.00"
  },
  "subscription": {
    "next_order_date": "2025-03-15",
    "skips_remaining": 3
  }
}
```

**Error Responses:**
- `400` - Missing subscription_id
- `403` - Skip not allowed (quota exceeded, too soon, etc.)
- `404` - Subscription not found
- `500` - Server error

---

## 2. Get Subscription Details

**Endpoint:** `GET /api/skips/subscriptions/{subscription_id}/`

**Example:** `/api/skips/subscriptions/gid://shopify/SubscriptionContract/SAMPLE123/`

**Response (200):**
```json
{
  "success": true,
  "subscription": {
    "id": "gid://shopify/SubscriptionContract/123",
    "name": "Monthly Coffee Subscription",
    "status": "active",
    "billing_cycle": "monthly",
    "next_order_date": "2025-02-15",
    "next_billing_date": "2025-02-15",
    "customer": {
      "email": "customer@example.com",
      "name": "John Doe"
    },
    "pricing": {
      "product_price": "29.99",
      "shipping_price": "5.00",
      "total_price": "34.99",
      "currency": "GBP"
    },
    "skip_info": {
      "can_skip": true,
      "skip_message": "Can skip",
      "skips_remaining": 4,
      "skips_used_this_year": 0,
      "consecutive_skips": 0,
      "max_skips_per_year": 4,
      "advance_notice_days": 7,
      "skip_fee": "0.00"
    },
    "recent_skips": []
  }
}
```

---

## 3. List Subscription Skips

**Endpoint:** `GET /api/skips/subscriptions/{subscription_id}/skips/`

**Response (200):**
```json
{
  "success": true,
  "subscription_id": "gid://shopify/SubscriptionContract/123",
  "total_skips": 2,
  "skips": [
    {
      "id": 2,
      "skip_type": "manual",
      "status": "confirmed",
      "original_order_date": "2025-01-15",
      "new_order_date": "2025-02-15",
      "reason": "Holiday",
      "skip_fee": "0.00",
      "created_at": "2025-01-08T10:30:00Z",
      "confirmed_at": "2025-01-08T10:30:05Z"
    }
  ]
}
```

---

## 4. Check Skip Quota

**Endpoint:** `GET /api/skips/subscriptions/{subscription_id}/skip-quota/`

**Response (200):**
```json
{
  "success": true,
  "has_skip_policy": true,
  "can_skip_next_order": true,
  "skip_message": "Can skip",
  "quota": {
    "max_skips_per_year": 4,
    "skips_used_this_year": 1,
    "skips_remaining": 3,
    "max_consecutive_skips": 2,
    "current_consecutive_skips": 0,
    "advance_notice_days": 7,
    "skip_fee": "0.00"
  }
}
```

---

## 5. Cancel Pending Skip

**Endpoint:** `DELETE /api/skips/skip/{skip_id}/cancel/` or `POST /api/skips/skip/{skip_id}/cancel/`

**Request (optional):**
```json
{
  "reason": "Changed my mind"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Skip successfully cancelled",
  "skip": {
    "id": 1,
    "status": "cancelled",
    "cancelled_at": "2025-01-10T14:20:00Z"
  }
}
```

---

## 6. List Customer Subscriptions

**Endpoint:** `GET /api/skips/subscriptions/`

**Query Parameters:**
- `email` - Customer email address
- `shopify_customer_id` - Shopify customer ID

**Examples:**
```
/api/skips/subscriptions/?email=customer@example.com
/api/skips/subscriptions/?shopify_customer_id=123
```

**Response (200):**
```json
{
  "success": true,
  "count": 2,
  "subscriptions": [
    {
      "id": "gid://shopify/SubscriptionContract/123",
      "name": "Monthly Coffee Subscription",
      "status": "active",
      "billing_cycle": "monthly",
      "next_order_date": "2025-02-15",
      "total_price": "34.99",
      "currency": "GBP",
      "skips_remaining": 3
    }
  ]
}
```

---

## 7. Health Check

**Endpoint:** `GET /api/skips/health/`

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-09T12:00:00Z",
  "service": "subscription-skips-api"
}
```

---

## Error Response Format

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation error)
- `403` - Forbidden (skip not allowed)
- `404` - Not Found
- `500` - Internal Server Error

---

## Testing with cURL

### Skip next payment:
```bash
curl -X POST http://localhost:8003/api/skips/skip/ \
  -H "Content-Type: application/json" \
  -d '{"subscription_id": "gid://shopify/SubscriptionContract/SAMPLE123", "reason": "Testing"}'
```

### Get subscription:
```bash
curl http://localhost:8003/api/skips/subscriptions/gid://shopify/SubscriptionContract/SAMPLE123/
```

### Check quota:
```bash
curl http://localhost:8003/api/skips/subscriptions/gid://shopify/SubscriptionContract/SAMPLE123/skip-quota/
```

### List skips:
```bash
curl http://localhost:8003/api/skips/subscriptions/gid://shopify/SubscriptionContract/SAMPLE123/skips/
```

### Cancel skip:
```bash
curl -X DELETE http://localhost:8003/api/skips/skip/1/cancel/
```

### List customer subscriptions:
```bash
curl "http://localhost:8003/api/skips/subscriptions/?email=sample@example.com"
```

### Health check:
```bash
curl http://localhost:8003/api/skips/health/
```

---

## JavaScript Fetch Examples

### Skip next payment:
```javascript
const response = await fetch('/api/skips/skip/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    subscription_id: 'gid://shopify/SubscriptionContract/123',
    reason: 'Going on vacation'
  })
});
const data = await response.json();
```

### Get subscription details:
```javascript
const response = await fetch('/api/skips/subscriptions/gid://shopify/SubscriptionContract/123/');
const data = await response.json();
```

### Check skip quota:
```javascript
const response = await fetch('/api/skips/subscriptions/gid://shopify/SubscriptionContract/123/skip-quota/');
const data = await response.json();
console.log(`Skips remaining: ${data.quota.skips_remaining}`);
```

---

## Admin Interface

**URL:** `http://localhost:8003/admin/skips/`

**Models:**
- Subscription Skip Policies
- Customer Subscriptions
- Subscription Skips
- Skip Notifications
- Skip Analytics

**Actions:**
- Confirm pending skips
- Cancel pending skips
- Reset skip quotas
- Sync to Shopify

---

## Authentication

Currently **no authentication required** for API endpoints. 

**Recommended for production:**
1. Add session authentication for customer-facing endpoints
2. Verify customer owns the subscription being modified
3. Add CSRF protection for POST/DELETE requests
4. Implement rate limiting to prevent abuse

---

## CORS Configuration

CORS is enabled for local development. For production:

**Update `core/settings.py`:**
```python
CORS_ALLOWED_ORIGINS = [
    'https://7fa66c-ac.myshopify.com',
    'https://your-custom-domain.com',
]
```

---

## Support

For issues or questions, see:
- Full documentation: `SUBSCRIPTION_SKIP_SYSTEM_COMPLETE.md`
- Summary: `SKIP_SYSTEM_SUMMARY.md`
- Django admin: http://localhost:8003/admin/skips/
