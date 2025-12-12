# 🚀 LAVISH LIBRARY - QUICK REFERENCE GUIDE

## ⚡ **SYSTEM AT A GLANCE**

### **What Is It?**
Subscription box e-commerce platform for book deliveries with Django backend + Shopify frontend

### **Key Components**
- **Shopify Store**: 7fa66c-ac.myshopify.com
- **Django Backend**: Port 8003
- **Liquid Theme**: Port 9292
- **Database**: SQLite (lavish_library.db)

---

## 🏁 **QUICK START**

### **Start Both Servers**
```bash
# Windows
START_BOTH_SERVERS.bat

# Or manually:
# Terminal 1 - Backend
cd app\lavish_backend
python manage.py runserver 8003

# Terminal 2 - Frontend
cd app\lavish_frontend
shopify theme dev --port 9292
```

### **Access Points**
- **Theme Preview**: http://127.0.0.1:9292
- **Django Admin**: http://127.0.0.1:8003/admin/
- **Shopify Store**: https://7fa66c-ac.myshopify.com

---

## 📦 **DJANGO APPS OVERVIEW**

| App | Purpose | Key Models |
|-----|---------|------------|
| `accounts` | User auth & profiles | CustomUser, CompanyRole |
| `customers` | Shopify customer sync | ShopifyCustomer, ShopifyCustomerAddress |
| `customer_subscriptions` | Subscription management | CustomerSubscription, SellingPlan |
| `orders` | Order processing | ShopifyOrder, ShopifyOrderLineItem |
| `products` | Product catalog | ShopifyProduct, ShopifyProductVariant |
| `inventory` | Stock management | ShopifyInventoryLevel, ShopifyLocation |
| `skips` | Skip/pause functionality | SubscriptionSkip, SkipPolicy |
| `shipping` | Shipping rates | ShopifyCarrierService, ShippingRate |
| `payments` | Payment tracking | ShopifyPaymentsAccount, ShopifyPayout |
| `locations` | Geographic data | Country, State, City |
| `email_manager` | Email automation | EmailTemplate, EmailHistory |
| `shopify_integration` | API integration | ShopifyStore, WebhookEndpoint |

---

## 🔌 **KEY API ENDPOINTS**

### **Location API**
```
GET  /api/locations/countries/              # All countries
GET  /api/locations/countries/{id}/states/  # States by country
GET  /api/locations/states/{id}/cities/     # Cities by state
GET  /api/locations/phone_codes/            # Phone codes
```

### **Customer API**
```
GET    /api/customers/                      # List customers
POST   /api/customers/addresses/create/     # Add address
PUT    /api/customers/addresses/{id}/update/ # Update address
DELETE /api/customers/addresses/{id}/delete/ # Delete address
```

### **Order API**
```
GET  /api/orders/                           # List orders
GET  /api/orders/customer-orders/?email=x   # Customer orders
POST /api/orders/{id}/update-address/       # Update order address
POST /api/orders/{id}/cancel/               # Cancel order
```

### **Subscription API**
```
GET   /api/subscriptions/selling-plans/     # List plans
POST  /api/subscriptions/checkout/create/   # Create subscription
PATCH /api/subscriptions/{id}/              # Update subscription
POST  /api/subscriptions/{id}/pause/        # Pause subscription
```

### **Skip API**
```
GET  /api/skips/                            # List skips
POST /api/skips/                            # Create skip
POST /api/skips/{id}/confirm/               # Confirm skip
POST /api/skips/{id}/cancel/                # Cancel skip
```

---

## 🎨 **FRONTEND KEY FILES**

### **Enhanced Account System**
- **Main Section**: `sections/enhanced-account.liquid`
- **Tabs**: Overview, Orders, Subscriptions, Addresses, Payments, Profile
- **JavaScript**: Inline (IIFE wrapped) + `assets/django-integration.js`

### **Other Sections**
- `sections/user-profile.liquid` - Personal info
- `sections/mfa-setup.liquid` - 2FA setup
- `sections/order-history.liquid` - Order list
- `sections/main-addresses.liquid` - Address book

### **JavaScript Integration**
- `assets/django-integration.js` - Django API communication
- Auto-detects dev/prod environment
- Handles location data (countries/states/cities)
- Tracks customer events

---

## 🔄 **DATA SYNC FLOW**

### **Django → Shopify (Push)**
```
1. Model save() detects changes
2. Sets needs_shopify_push = True
3. Background sync task runs
4. GraphQL mutation to Shopify
5. Update last_pushed_to_shopify
```

### **Shopify → Django (Webhook)**
```
1. Shopify sends webhook (POST)
2. Django verifies HMAC signature
3. Create/update Django model
4. Set skip_push_flag = True (avoid loop)
5. Update last_synced_from_shopify
```

### **Key Sync Models**
All have these fields:
- `shopify_id` - Shopify identifier
- `needs_shopify_push` - Push pending flag
- `last_pushed_to_shopify` - Push timestamp
- `last_synced_from_shopify` - Pull timestamp
- `shopify_push_error` - Error message

---

## 📋 **COMMON TASKS**

### **1. Add New Country/State/City Data**
```bash
python manage.py populate_countries
# Edit: locations/management/commands/populate_countries.py
```

### **2. Sync Customers from Shopify**
```python
from shopify_integration.client import ShopifyAPIClient
from customers.sync import sync_customers

client = ShopifyAPIClient()
sync_customers(client)
```

### **3. Create a Selling Plan**
```python
from customer_subscriptions.models import SellingPlan

plan = SellingPlan.objects.create(
    name="Monthly Deluxe Box",
    billing_interval="MONTH",
    billing_interval_count=1,
    delivery_interval="MONTH",
    delivery_interval_count=1,
    price_adjustment_type="FIXED_AMOUNT",
    price_adjustment_value=49.99,
    is_active=True
)
# Will auto-push to Shopify
```

### **4. Process a Skip Request**
```python
from skips.models import SubscriptionSkip

skip = SubscriptionSkip.objects.create(
    subscription_id=123,
    original_order_date="2025-01-15",
    original_billing_date="2025-01-15",
    new_order_date="2025-02-15",
    new_billing_date="2025-02-15",
    reason="On vacation",
    status="pending"
)

skip.confirm_skip()  # Updates subscription dates
```

### **5. Update Inventory**
```python
from inventory.models import ShopifyInventoryLevel

level = ShopifyInventoryLevel.objects.get(
    inventory_item__sku="DELUXE-JAN-2025",
    location__name="Sydney Warehouse"
)

level.available = 100
level.save()  # Will auto-push to Shopify
```

### **6. Test Django API Locally**
```bash
# Get countries
curl http://127.0.0.1:8003/api/locations/countries/

# Get customer orders
curl http://127.0.0.1:8003/api/orders/customer-orders/?customer_email=test@example.com

# Create address
curl -X POST http://127.0.0.1:8003/api/customers/addresses/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "gid://shopify/Customer/123",
    "first_name": "John",
    "address1": "123 Main St",
    "city": "Sydney",
    "country": "Australia"
  }'
```

---

## 🐛 **DEBUGGING**

### **Check Django Logs**
```bash
tail -f app/lavish_backend/logs/django.log
```

### **Check Browser Console**
Open DevTools (F12) → Console tab
Look for messages from `django-integration.js`

### **Common Issues**

#### **"Error loading countries"**
- Check Django server is running on port 8003
- Verify `populate_countries` command was run
- Check CORS settings in `settings.py`
- Check browser console for API errors

#### **"showTab is not defined"**
- Check Liquid syntax in `enhanced-account.liquid`
- Ensure IIFE wrapper is intact
- Check for template literal conflicts

#### **Sync Not Working**
- Check `needs_shopify_push` flag in database
- Verify Shopify credentials in `.env`
- Check `shopify_push_error` field for error messages
- Review sync logs in Django Admin

#### **Address Not Saving**
- Check form validation in frontend
- Check API endpoint response in Network tab
- Verify address model fields match API request
- Check for database errors in Django logs

---

## ⚙️ **CONFIGURATION**

### **Environment Variables** (`.env`)
```env
# Shopify
SHOPIFY_STORE_URL=7fa66c-ac.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
SHOPIFY_API_KEY=xxxxx
SHOPIFY_API_SECRET=xxxxx
SHOPIFY_API_VERSION=2025-01

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### **Django Settings** (`core/settings.py`)

**Development:**
```python
DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Production:**
```python
DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://7fa66c-ac.myshopify.com",
    "https://lavishlibrary.com.au",
]
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

---

## 📊 **DATABASE SCHEMA**

### **Core Relationships**
```
Customer → Addresses (1:N)
Customer → Subscriptions (1:N)
Customer → Orders (1:N)

Subscription → Skips (1:N)
Subscription → SellingPlan (N:1)
Subscription → BillingAttempts (1:N)

Order → LineItems (1:N)
Order → Addresses (1:N)

Product → Variants (1:N)
Product → Images (1:N)
Product → SellingPlans (N:M)

Variant → InventoryItem (1:1)
InventoryItem → InventoryLevels (1:N)

Location → InventoryLevels (1:N)

Country → States (1:N)
State → Cities (1:N)
```

---

## 🚢 **DEPLOYMENT**

### **Frontend (Shopify Theme)**
```bash
# Test locally
shopify theme dev

# Push to Shopify (unpublished)
shopify theme push --unpublished

# Publish
shopify theme publish
```

### **Backend (Django)**
```bash
# Production checklist
1. Set DEBUG = False
2. Update ALLOWED_HOSTS
3. Configure production database (PostgreSQL)
4. Collect static files: python manage.py collectstatic
5. Run migrations: python manage.py migrate
6. Set up Gunicorn/uWSGI
7. Configure Nginx
8. Set up SSL (Let's Encrypt)
9. Configure systemd service
10. Set up Cloudflare Tunnel
```

---

## 🔐 **SECURITY NOTES**

### **Current Setup**
- ✅ CORS configured
- ✅ CSRF protection (disabled for API dev)
- ✅ Webhook HMAC verification
- ✅ Environment variables for secrets
- ❌ **API Authentication**: AllowAny (dev only)

### **Production TODO**
- [ ] Enable API authentication (JWT tokens)
- [ ] Enable CSRF for state-changing operations
- [ ] Rate limiting on API endpoints
- [ ] Regular security audits
- [ ] Automated backups
- [ ] Log monitoring (Sentry)

---

## 📞 **TROUBLESHOOTING CONTACTS**

### **Django Backend Issues**
1. Check logs: `app/lavish_backend/logs/django.log`
2. Review Django Admin: http://127.0.0.1:8003/admin/
3. Check Sync Operations: Shopify Integration → Sync Operations

### **Shopify Integration Issues**
1. Check webhook logs: Shopify Admin → Settings → Notifications
2. Verify API credentials in `.env`
3. Check API rate limits: Django Admin → API Rate Limits

### **Frontend Issues**
1. Check browser console (F12)
2. Review Liquid syntax: `shopify theme check`
3. Test JavaScript: Add `console.log()` statements

---

## 📚 **USEFUL COMMANDS**

### **Django Management**
```bash
python manage.py migrate                # Run migrations
python manage.py makemigrations         # Create migrations
python manage.py createsuperuser        # Create admin user
python manage.py populate_countries     # Load location data
python manage.py test                   # Run tests
python manage.py shell                  # Django shell
python manage.py dbshell                # Database shell
python manage.py collectstatic          # Collect static files
```

### **Shopify CLI**
```bash
shopify theme dev                       # Start dev server
shopify theme push                      # Push theme
shopify theme pull                      # Pull theme
shopify theme publish                   # Publish theme
shopify theme check                     # Check for errors
shopify theme list                      # List themes
```

### **Database**
```bash
# Backup
python manage.py dumpdata > backup.json

# Restore
python manage.py loaddata backup.json

# Reset database (dev only!)
rm lavish_library.db
python manage.py migrate
python manage.py populate_countries
python manage.py createsuperuser
```

---

## 🎯 **FEATURE FLAGS**

### **Implemented ✅**
- Bidirectional Shopify sync
- Customer management
- Subscription management
- Skip functionality
- Address management
- Order processing
- Inventory tracking
- Email automation
- Multi-currency support
- Location services

### **Planned 📝**
- API authentication
- Caching (Redis)
- Celery background tasks
- Analytics dashboard
- Customer portal enhancements
- Mobile app API
- Advanced reporting

---

## 📖 **DOCUMENTATION**

- **Full Analysis**: `COMPREHENSIVE_SYSTEM_ANALYSIS.md`
- **This Guide**: `QUICK_REFERENCE_GUIDE.md`
- **Frontend README**: `app/lavish_frontend/README.md`
- **Backend README**: `README.md`

---

**Last Updated**: December 12, 2025  
**Version**: 1.0  
**Project**: Lavish Library

