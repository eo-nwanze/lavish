# Quick Start: Shipping & Currency Integration

## ⚡ 5-Minute Setup

### 1. Configure Environment Variables

Create/update `app/lavish_backend/.env`:

```env
# Shopify (required)
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxx
SHOPIFY_API_KEY=xxxxxxxxxxxxx
SHOPIFY_API_SECRET=xxxxxxxxxxxxx

# Sendal Shipping (optional - falls back to static rates)
SENDAL_API_ENDPOINT=https://api.sendal.com/v1/rates
SENDAL_API_KEY=your_sendal_key

# Exchange Rate API (optional - uses approximate rates if missing)
EXCHANGE_RATE_API_KEY=your_exchangerate_api_key
```

### 2. Register Carrier Service in Shopify

```bash
curl -X POST https://7fa66c-ac.myshopify.com/admin/api/2024-10/carrier_services.json \
  -H "X-Shopify-Access-Token: YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "carrier_service": {
      "name": "Lavish Shipping",
      "callback_url": "https://lavish-backend.endevops.net/api/shipping/calculate-rates/",
      "service_discovery": true,
      "active": true
    }
  }'
```

**Save the returned carrier_service.id to Django:**

```python
python manage.py shell
>>> from shipping.models import ShopifyCarrierService
>>> ShopifyCarrierService.objects.create(
...     shopify_id=123456,  # From API response
...     name='Lavish Shipping',
...     callback_url='https://lavish-backend.endevops.net/api/shipping/calculate-rates/',
...     service_discovery=True,
...     active=True
... )
```

### 3. Test It

```bash
cd app/lavish_backend
python manage.py runserver 8003
```

**Test locally:**
```bash
curl -X POST http://localhost:8003/api/shipping/test-rates/ \
  -H "Content-Type: application/json" \
  -d '{
    "origin_country": "US",
    "origin_postal_code": "10001",
    "destination_country": "US",
    "destination_postal_code": "90210",
    "weight_grams": 1000,
    "value_cents": 2999,
    "currency": "USD"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "response": {
    "rates": [
      {"service_name": "Standard Shipping", "total_price": "599", "currency": "USD"},
      {"service_name": "Express Shipping", "total_price": "1599", "currency": "USD"},
      {"service_name": "Overnight Shipping", "total_price": "2999", "currency": "USD"}
    ]
  }
}
```

### 4. Test on Shopify

1. Go to your Shopify store
2. Add a product to cart
3. Proceed to checkout
4. Enter shipping address
5. See "Lavish Shipping" rates appear!

---

## 📋 What You Get

### ✅ Working Right Now (No API Keys Needed)
- Static shipping rates for all countries
- Multi-currency conversion (10 currencies)
- Automatic locale detection
- Template currency variables
- Test endpoints

### 🔑 When You Add API Keys
- **Sendal API**: Live rates with duties & taxes
- **Exchange Rate API**: Real-time currency conversion

### 💰 Shipping Rates (Static Fallback)

| Country | Standard | Express | Overnight |
|---------|----------|---------|-----------|
| US | $5.99 | $15.99 | $29.99 |
| Canada | $8.99 | $18.99 | $34.99 |
| UK | $9.99 | $19.99 | $39.99 |
| Australia | $12.99 | $22.99 | $44.99 |
| EU | $10.99 | $20.99 | $40.99 |
| Other | $15.00 | $30.00 | $50.00 |

*Auto-converts to customer's currency*

### 🌍 Supported Currencies

USD, EUR, GBP, CAD, AUD, JPY, CNY, CHF, SEK, NZD

---

## 🚀 API Endpoints

### Shopify Webhook (Production)
```
POST https://lavish-backend.endevops.net/api/shipping/calculate-rates/
```

### Test Endpoint (Development)
```
POST http://localhost:8003/api/shipping/test-rates/
```

### List Carriers
```
GET http://localhost:8003/api/shipping/carriers/
```

---

## 🧪 Test Commands

**Run test suite:**
```bash
python test_shipping_rates.py
```

**Django shell test:**
```python
python manage.py shell
>>> from shipping.shopify_shipping_service import ShopifyShippingRateCalculator
>>> calc = ShopifyShippingRateCalculator()
>>> # See test_shipping_rates.py for full example
```

---

## 🔍 Debugging

**Check Django logs:**
```bash
python manage.py runserver 8003
# Watch for: "Received shipping rate request from Shopify"
```

**Check cache:**
```python
python manage.py shell
>>> from django.core.cache import cache
>>> cache.get('shipping_rates_10001_90210_1000_2999_USD')
```

**Clear cache:**
```python
>>> cache.clear()
```

---

## 📞 Get Help

**Full Documentation:** `SHIPPING_CURRENCY_INTEGRATION_COMPLETE.md`

**Key Sections:**
- Shopify Integration (Step-by-step)
- Testing Guide
- Environment Variables
- Troubleshooting
- API Request/Response Format

---

## ✨ That's It!

Your shipping integration is **ready to go**. Just add API keys when available, and you'll get live rates automatically. Until then, the static fallback rates work perfectly for development and even production.

**Questions?** Check the full documentation or the code comments - everything is documented inline.
