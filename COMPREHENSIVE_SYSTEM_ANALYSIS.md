# 🔍 COMPREHENSIVE SYSTEM ANALYSIS - LAVISH LIBRARY

## 📋 **TABLE OF CONTENTS**
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Django Backend Features](#django-backend-features)
4. [Shopify Integration](#shopify-integration)
5. [Frontend (Liquid Theme)](#frontend-liquid-theme)
6. [Data Flow & Synchronization](#data-flow--synchronization)
7. [API Endpoints](#api-endpoints)
8. [Database Models](#database-models)
9. [Key Functionalities](#key-functionalities)
10. [Development & Deployment](#development--deployment)

---

## 🏢 **SYSTEM OVERVIEW**

**Lavish Library** is a sophisticated subscription box e-commerce platform integrating:
- **Shopify Store** (7fa66c-ac.myshopify.com)
- **Django Backend** (Custom API & Admin)
- **Enhanced Liquid Theme** (Custom customer portal)

### **Core Purpose**
Manage subscription-based book box deliveries with:
- Monthly/recurring billing
- Customer address management
- Order tracking & fulfillment
- Skip/pause functionality
- Inventory synchronization
- Multi-currency support

### **Technology Stack**
- **Frontend**: Shopify Liquid, JavaScript ES6+, CSS3
- **Backend**: Django 4.2.23, Django REST Framework
- **Database**: SQLite (dev), PostgreSQL-ready
- **API**: Shopify Admin API (GraphQL & REST), Custom REST API
- **Integrations**: Sendal Shipping, Exchange Rate API
- **Admin UI**: Jazzmin (customized)
- **Timezone**: Australia/Sydney (AEDT/AEST)

---

## 🏗️ **ARCHITECTURE**

### **System Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    SHOPIFY STORE                             │
│         (7fa66c-ac.myshopify.com)                           │
│  - Product Catalog                                           │
│  - Checkout & Payments                                       │
│  - Customer Authentication                                   │
│  - Order Processing                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Webhooks & API Calls
                     │
┌────────────────────┴────────────────────────────────────────┐
│              DJANGO BACKEND (Port 8003)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ REST API Layer                                        │   │
│  │  - /api/customers/    - Customer CRUD                 │   │
│  │  - /api/orders/       - Order management             │   │
│  │  - /api/subscriptions/- Subscription sync            │   │
│  │  - /api/locations/    - Country/State/City data      │   │
│  │  - /api/skips/        - Skip management              │   │
│  │  - /api/products/     - Product catalog              │   │
│  │  - /api/inventory/    - Stock levels                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Core Applications                                     │   │
│  │  - accounts          - User auth & profiles          │   │
│  │  - customers         - Shopify customer sync         │   │
│  │  - orders            - Order tracking                │   │
│  │  - products          - Product management            │   │
│  │  - customer_subscriptions - Subscription contracts   │   │
│  │  - skips             - Delivery skip logic           │   │
│  │  - inventory         - Stock management              │   │
│  │  - shipping          - Delivery profiles             │   │
│  │  - payments          - Payment tracking              │   │
│  │  - locations         - Geographic data               │   │
│  │  - email_manager     - Email automation              │   │
│  │  - shopify_integration - API client & webhooks       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Data Layer (SQLite)                                   │   │
│  │  - lavish_library.db                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ AJAX/Fetch API
                     │
┌────────────────────┴────────────────────────────────────────┐
│         SHOPIFY LIQUID THEME (Port 9292)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Enhanced Account Pages                                │   │
│  │  - sections/enhanced-account.liquid                  │   │
│  │  - sections/user-profile.liquid                      │   │
│  │  - sections/order-history.liquid                     │   │
│  │  - sections/mfa-setup.liquid                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ JavaScript Integration                                │   │
│  │  - assets/django-integration.js (Backend comm)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### **Data Flow Architecture**

1. **Customer Action** → Shopify Theme (Liquid + JS)
2. **Frontend JS** → Django REST API (HTTP/JSON)
3. **Django Processing** → Database Operations
4. **Bidirectional Sync** → Shopify Admin API (GraphQL)
5. **Webhook Events** → Django Backend → Database Update

---

## 🖥️ **DJANGO BACKEND FEATURES**

### **1. Customer Management** (`customers` app)

#### **Models**
- **`ShopifyCustomer`**
  - Syncs with Shopify customer data
  - Fields: email, name, phone, tags, marketing preferences
  - Order stats: total_spent, number_of_orders
  - Bidirectional sync tracking
  - Local user association (optional)

- **`ShopifyCustomerAddress`**
  - Multiple addresses per customer
  - Default address flagging
  - Geographic codes (country_code, province_code)
  - Auto-push changes to Shopify
  - Used for order fulfillment

- **`CustomerSyncLog`**
  - Audit trail for all sync operations
  - Error tracking and debugging
  - Performance metrics

#### **Key Functionalities**
- ✅ Import customers from Shopify (bulk & incremental)
- ✅ Create/update customers in Django → Push to Shopify
- ✅ Address CRUD with automatic Shopify sync
- ✅ Customer search by email, name, tags
- ✅ Marketing preference management
- ✅ Customer segmentation via tags

---

### **2. Subscription Management** (`customer_subscriptions` app)

#### **Models**

**`SellingPlan`**
- Subscription product configurations
- Billing policy (RECURRING, ON_PURCHASE)
- Billing interval (DAY, WEEK, MONTH, YEAR)
- Delivery policy & schedule
- Price adjustments (percentage, fixed amount, or price)
- Product associations (many-to-many)
- Shopify SellingPlan sync

**`CustomerSubscription`**
- Maps to Shopify SubscriptionContract
- Status: ACTIVE, PAUSED, CANCELLED, EXPIRED, FAILED
- Next billing & delivery dates
- Line items (products in subscription)
- Delivery address (JSON)
- Payment method reference
- Billing cycle tracking
- Trial period support

**`SubscriptionAddress`**
- Primary subscription delivery address per customer
- Auto-propagates to unshipped orders
- Address validation support
- Change tracking (who updated, when)

**`OrderAddressOverride`**
- One-time address override for specific order
- Reason tracking
- Temporary vs permanent flag
- Does not affect primary subscription address

**`ProductShippingConfig`**
- Per-product cutoff configuration
- Cutoff days before shipping (default: 7)
- Reminder days before cutoff (default: 14)
- Processing time & transit estimates
- International shipping restrictions
- Special handling requirements

**`ShippingCutoffLog`**
- Notification log for cutoff reminders
- Types: REMINDER, CUTOFF, SHIPPED
- Email & SMS tracking
- Delivery status

**`SubscriptionBillingAttempt`**
- Tracks all billing attempts
- Status: SUCCESS, FAILED, PENDING
- Created order reference (if successful)
- Error messages for failed attempts
- Amount & currency

**`SubscriptionSyncLog`**
- Django ↔ Shopify sync operations
- Import/export tracking
- Error details and statistics

#### **Key Functionalities**
- ✅ Create selling plans in Django → Push to Shopify
- ✅ Import Shopify subscription contracts
- ✅ Update subscription status (pause, cancel, resume)
- ✅ Modify line items & quantities
- ✅ Change billing/delivery dates
- ✅ Address updates with order propagation
- ✅ Per-order address overrides
- ✅ Cutoff date calculations
- ✅ Automatic cutoff reminders
- ✅ Billing attempt tracking

---

### **3. Skip Management** (`skips` app)

#### **Models**

**`SubscriptionSkipPolicy`**
- Configurable skip rules
- Max skips per year (default: 4)
- Max consecutive skips (default: 2)
- Advance notice requirement (default: 7 days)
- Optional skip fees

**`SubscriptionSkip`**
- Individual skip records
- Original vs new dates (billing & delivery)
- Skip reasons & details
- Status: pending, confirmed, cancelled, failed
- Fee tracking & refunds
- Shopify order reference
- Admin notes

**`SkipNotification`**
- Notification log for skip events
- Types: skip_confirmed, skip_reminder, skip_expiring, skip_limit_reached
- Multi-channel (email, SMS, push)
- Delivery tracking

**`SkipAnalytics`**
- Aggregated skip analytics
- Period types: daily, weekly, monthly, yearly
- Skip metrics & financial impact
- Customer behavior analysis
- Top skip reasons

#### **Key Functionalities**
- ✅ Customer-initiated skips with reason capture
- ✅ Policy enforcement (max skips, advance notice)
- ✅ Automatic date rescheduling
- ✅ Skip fee calculation & charging
- ✅ Email/SMS notifications
- ✅ Skip cancellation (before confirmation)
- ✅ Analytics & reporting
- ✅ Admin override capabilities

---

### **4. Order Management** (`orders` app)

#### **Models**

**`ShopifyOrder`**
- Complete order data from Shopify
- Financial status: pending, paid, refunded, etc.
- Fulfillment status: fulfilled, partial, unfulfilled
- Pricing breakdown (total, subtotal, tax, shipping)
- Customer relationship
- Tags & notes
- Sync tracking

**`ShopifyOrderLineItem`**
- Order line items (products)
- Product & variant references
- Quantity, price, discounts
- Custom properties (JSON)
- SKU tracking

**`ShopifyOrderAddress`**
- Shipping & billing addresses
- Separate records per order
- Full address details with geocodes

**`OrderSyncLog`**
- Order sync operation logging
- Statistics & error tracking

#### **Key Functionalities**
- ✅ Import orders from Shopify (bulk & webhook)
- ✅ Order filtering & search
- ✅ Customer order history
- ✅ Order address updates
- ✅ Order cancellation (with restrictions)
- ✅ Invoice generation
- ✅ Financial & fulfillment status tracking
- ✅ Tag-based order segmentation

---

### **5. Product Management** (`products` app)

#### **Models**

**`ShopifyProduct`**
- Product catalog from Shopify
- Title, handle, description
- Product type, vendor
- Status: ACTIVE, ARCHIVED, DRAFT
- SEO fields
- Tags (JSON array)
- Bidirectional sync
- Created-in-Django flag

**`ShopifyProductVariant`**
- Product variations
- SKU, barcode
- Pricing (price, compare_at_price, cost)
- Inventory settings
- Physical properties (weight)
- Options (option1, option2, option3)
- Position ordering

**`ShopifyProductImage`**
- Product images
- Image URL, alt text, dimensions
- Position ordering
- Variant associations

**`ShopifyProductMetafield`**
- Custom product metadata
- Namespace & key organization
- Various value types
- Used for custom product data

**`ProductSyncLog`**
- Product sync logging
- Variant & image processing stats

#### **Key Functionalities**
- ✅ Import products from Shopify
- ✅ Create products in Django → Push to Shopify
- ✅ Update product details (title, description, price)
- ✅ Manage variants & options
- ✅ Image management with positioning
- ✅ Metafield support for custom data
- ✅ Product search & filtering
- ✅ Tag-based organization
- ✅ Auto-generate product handles

---

### **6. Inventory Management** (`inventory` app)

#### **Models**

**`ShopifyLocation`**
- Warehouse/fulfillment locations
- Address details
- Active status & capabilities
- Fulfillment service association

**`ShopifyInventoryItem`**
- Inventory items (linked to variants)
- SKU tracking
- Cost information
- Tracking settings

**`ShopifyInventoryLevel`**
- Stock levels per location
- Available, committed, incoming quantities
- On-hand totals
- Bidirectional sync
- Auto-push quantity changes

**`InventoryAdjustment`**
- Manual inventory adjustments
- Adjustment types: increase, decrease, recount, correction
- Before/after quantities
- Reason & notes
- User tracking

**`InventorySyncLog`**
- Inventory sync logging

#### **Key Functionalities**
- ✅ Real-time inventory sync with Shopify
- ✅ Multi-location inventory tracking
- ✅ Stock level updates (Django → Shopify)
- ✅ Low stock alerts
- ✅ Inventory adjustments with audit trail
- ✅ Automatic restock notifications
- ✅ Committed quantity tracking
- ✅ Incoming inventory management

---

### **7. Location Services** (`locations` app)

#### **Models**

**`Country`**
- Country master data
- ISO codes (alpha-2 & alpha-3)
- Phone codes (international dialing)
- Currency & symbol
- Timezone
- Flag emoji

**`State`**
- States/provinces within countries
- State codes
- Hierarchical relationship

**`City`**
- Cities within states
- Latitude/longitude coordinates
- Hierarchical relationship

#### **Key Functionalities**
- ✅ Country/state/city dropdown population
- ✅ Phone code lookup by country
- ✅ Currency detection by country
- ✅ Address validation support
- ✅ Geographic search & filtering
- ✅ Timezone management
- ✅ Multi-currency support (10 currencies)

---

### **8. Shipping Management** (`shipping` app)

#### **Models**

**`ShopifyCarrierService`**
- Custom carrier services
- API callback configuration
- Rate calculation support

**`ShopifyDeliveryProfile`**
- Delivery profile configurations
- Default profile flagging
- Location associations

**`ShopifyDeliveryZone`**
- Geographic delivery zones
- Country coverage (JSON array)
- Zone-specific settings

**`ShopifyDeliveryMethod`**
- Shipping methods per zone
- Method types: shipping, pickup
- Delivery date estimates

**`ShippingRate`**
- Dynamic shipping rates
- Carrier & method associations
- Price calculations
- Weight-based pricing

#### **Key Functionalities**
- ✅ Custom shipping rate calculation
- ✅ Multi-zone delivery management
- ✅ Carrier service integration (Sendal API)
- ✅ Pickup location support
- ✅ Delivery date estimates
- ✅ Weight-based rate calculation
- ✅ Free shipping thresholds

---

### **9. Shopify Integration** (`shopify_integration` app)

#### **Models**

**`ShopifyStore`**
- Store configuration
- API credentials (key, secret, token)
- API version
- Store settings (currency, timezone, country)
- Last sync timestamp

**`WebhookEndpoint`**
- Webhook configurations
- Topics (orders/create, customers/update, etc.)
- Endpoint URLs
- Format (JSON/XML)
- Active status

**`SyncOperation`**
- Sync operation tracking
- Operation types: customers, products, orders, inventory, full
- Progress tracking (total, processed, errors)
- Status: pending, running, completed, failed
- Timing & duration
- Error details (JSON)

**`APIRateLimit`**
- Rate limit tracking
- API types: REST, GraphQL
- Current calls vs max calls
- Window timing
- Throttle status

#### **Core Components**

**`ShopifyAPIClient`** (client.py)
- GraphQL & REST API communication
- Automatic rate limit handling
- Retry logic with exponential backoff
- Pagination support (cursor-based)
- Error handling & logging
- Bulk operation support

#### **Key Functionalities**
- ✅ Full Shopify API integration
- ✅ Webhook management & handling
- ✅ Rate limit tracking & throttling
- ✅ Bulk operations for large datasets
- ✅ Real-time event processing
- ✅ Error recovery & retry logic
- ✅ Sync operation monitoring
- ✅ Multi-store support (architecture ready)

---

### **10. Email Management** (`email_manager` app)

#### **Features**
- ✅ Email templates (subscription reminders, skip confirmations, etc.)
- ✅ Email history & tracking
- ✅ Scheduled emails
- ✅ Email automation rules
- ✅ Inbox management
- ✅ Attachment handling
- ✅ Security alerts
- ✅ Email folders & labels
- ✅ Spam filtering (EmailGuardian)

---

### **11. User Management** (`accounts` app)

#### **Custom User Model**
- Extended Django user with additional fields
- Company roles & permissions
- Payment details (bank, card, PayID)
- Industry type associations
- User sessions tracking
- Company site management

#### **Key Functionalities**
- ✅ Custom authentication backends
- ✅ Face recognition authentication (experimental)
- ✅ MFA/2FA support
- ✅ Role-based access control
- ✅ Session management
- ✅ Payment method storage

---

## 🔌 **SHOPIFY INTEGRATION**

### **Bidirectional Sync Strategy**

#### **Django → Shopify (Push)**
1. **Trigger**: Model save() with change detection
2. **Flag**: `needs_shopify_push = True`
3. **Processing**: Background task or manual sync
4. **API Call**: GraphQL mutation to Shopify
5. **Result**: Update `last_pushed_to_shopify` timestamp
6. **Error Handling**: Store error in `shopify_push_error`

#### **Shopify → Django (Pull/Webhook)**
1. **Webhook Event**: Shopify sends POST to Django endpoint
2. **Verification**: HMAC signature validation
3. **Processing**: Create/update Django model
4. **Flag**: Set `skip_push_flag` to avoid circular sync
5. **Timestamp**: Update `last_synced_from_shopify`

### **Webhook Topics Handled**
- `customers/create` - New customer registration
- `customers/update` - Customer profile changes
- `customers/delete` - Customer deletion
- `orders/create` - New order placement
- `orders/updated` - Order status changes
- `orders/cancelled` - Order cancellations
- `subscription_contracts/create` - New subscription
- `subscription_contracts/update` - Subscription changes
- `subscription_billing_attempts/success` - Successful billing
- `subscription_billing_attempts/failure` - Failed billing
- `products/create` - New product
- `products/update` - Product changes
- `inventory_levels/update` - Stock changes

### **API Endpoints Used**

#### **GraphQL Queries**
- `customers` - Customer list with pagination
- `customer` - Single customer details
- `subscriptionContracts` - Subscription list
- `subscriptionContract` - Single subscription
- `products` - Product catalog
- `productVariants` - Variant details
- `orders` - Order history
- `inventoryLevels` - Stock levels

#### **GraphQL Mutations**
- `customerCreate` - Create customer
- `customerUpdate` - Update customer
- `customerAddressCreate` - Add address
- `subscriptionContractCreate` - New subscription
- `subscriptionContractUpdate` - Modify subscription
- `subscriptionBillingAttemptCreate` - Trigger billing
- `productCreate` - Create product
- `inventoryAdjustQuantities` - Update stock

#### **REST Endpoints**
- `/admin/api/2025-01/customers.json` - Customer operations
- `/admin/api/2025-01/orders.json` - Order operations
- `/admin/api/2025-01/products.json` - Product operations
- `/admin/api/2025-01/inventory_levels.json` - Inventory operations

---

## 🎨 **FRONTEND (LIQUID THEME)**

### **Enhanced Account System**

#### **Main Section: `enhanced-account.liquid`**

**Features:**
- Tabbed interface (6 tabs):
  1. **Overview** - Account summary, stats
  2. **Orders** - Order history (upcoming, all, cancelled)
  3. **Subscriptions** - Active & cancelled subscriptions
  4. **Addresses** - Manage delivery addresses
  5. **Payment Methods** - Payment info (Shopify managed)
  6. **User Profile** - Personal details & settings

**Tab Structure:**
```liquid
<div class="account-tabs">
  <a onclick="showTab('overview')">Overview</a>
  <a onclick="showTab('orders')">Orders</a>
  <a onclick="showTab('subscriptions')">Subscriptions</a>
  <a onclick="showTab('addresses')">Addresses</a>
  <a onclick="showTab('payments')">Payment Methods</a>
  <a onclick="showTab('profile')">User Profile</a>
</div>

<div id="overview" class="tab-content">...</div>
<div id="orders" class="tab-content">...</div>
<!-- ... other tabs -->
```

**Dynamic Features:**
- Real-time data from `{{ customer }}` Liquid object
- Modal wizards for data entry (addresses, subscriptions)
- Inline JavaScript for tab navigation (IIFE wrapped)
- AJAX calls to Django backend via `django-integration.js`
- Responsive design (mobile-first)
- Empty state messages when no data

**Modals:**
1. **Add New Address Modal** - Multi-step form
2. **Edit Address Modal** - Pre-filled form
3. **Add Payment Method Modal** - Shopify checkout redirect
4. **Edit Subscription Modal** - Subscription management
5. **Cancel Subscription Modal** - Cancellation flow

---

### **JavaScript Integration**

#### **`django-integration.js`**

**Purpose**: Bridge between Liquid theme and Django REST API

**Key Methods:**

```javascript
class DjangoIntegration {
    constructor() {
        // Auto-detect environment (dev/prod)
        this.baseUrl = (localhost || myshopify) 
            ? 'http://127.0.0.1:8003/api' 
            : 'https://lavish-backend.endevops.net/api';
    }

    // Core Methods
    async makeRequest(endpoint, method='GET', data=null) { }
    async loadLocationData() { }
    async populateCountryDropdowns() { }
    async handleCountryChange(selectElement) { }
    async handleStateChange(selectElement) { }
    
    // Tracking Methods
    trackPageView() { }
    trackAddToCart(event) { }
    trackFormSubmission(event) { }
    trackCustomer(customer) { }
}
```

**Location Data Flow:**
1. On page load → `loadLocationData()`
2. Fetch `/api/locations/countries/` → Store in memory
3. Fetch `/api/locations/phone_codes/` → Store in memory
4. Populate dropdowns → `populateCountryDropdowns()`
5. Listen for changes → `handleCountryChange()` → Fetch states
6. Listen for changes → `handleStateChange()` → Fetch cities

**Address Form Integration:**
- Targets: `#addr_country`, `#edit_addr_country`, `#change_addr_country`
- Cascading dropdowns: Country → State → City
- Phone code dropdown synced with country selection
- Error handling with user-friendly messages

---

### **Other Key Sections**

#### **`user-profile.liquid`**
- Personal information editing
- Marketing preferences
- Account settings
- Password change (Shopify managed)

#### **`mfa-setup.liquid`**
- Multi-factor authentication setup
- QR code display for authenticator apps
- Verification code entry
- Backup codes generation

#### **`order-history.liquid`**
- Detailed order list
- Order status tracking
- Reorder functionality
- Invoice downloads

#### **`main-addresses.liquid`**
- Address book management
- Default address selection
- Add/edit/delete addresses
- Address validation

---

## 🔄 **DATA FLOW & SYNCHRONIZATION**

### **Example: Customer Address Update**

#### **Scenario**: Customer updates their subscription address

**Frontend (Liquid) Flow:**
```
1. Customer clicks "Edit" on address
2. Modal opens with pre-filled data
3. Customer modifies address fields
4. JavaScript validates input
5. AJAX POST to Django: /api/customers/addresses/{id}/update/
```

**Django Backend Flow:**
```python
6. API view receives request
7. Find ShopifyCustomerAddress by ID
8. Update address fields from request data
9. Save model:
   - save() method detects changes
   - Sets needs_shopify_push = True
   - Saves to database
10. Return success response to frontend
```

**Background Sync (Django → Shopify):**
```python
11. Sync task finds records with needs_shopify_push = True
12. ShopifyAPIClient.execute_graphql_query()
13. GraphQL mutation: customerAddressUpdate
14. Shopify processes update
15. Django updates:
    - last_pushed_to_shopify = now()
    - needs_shopify_push = False
    - Clear shopify_push_error
```

**Webhook Response (Shopify → Django):**
```python
16. Shopify sends webhook: customers/update
17. Django webhook handler receives POST
18. Verify HMAC signature
19. Update ShopifyCustomer model:
    - Parse webhook JSON
    - Update fields
    - Save with skip_push_flag = True (avoid circular sync)
    - Update last_synced_from_shopify
```

### **Sync Conflict Resolution**
- **Timestamp Comparison**: Last modified wins
- **Manual Review**: Flag conflicts for admin review
- **Shopify as Source of Truth**: For core data (orders, payments)
- **Django as Extension**: For custom data (skips, analytics)

---

## 📡 **API ENDPOINTS**

### **Location API** (`/api/locations/`)

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/countries/` | GET | List all countries with states/cities | Country array |
| `/countries/{id}/states/` | GET | Get states for country | State array |
| `/states/{id}/cities/` | GET | Get cities for state | City array |
| `/phone_codes/` | GET | Get phone codes for all countries | Phone code array |

**Example Response:**
```json
{
  "id": 1,
  "name": "Australia",
  "iso_code": "AU",
  "phone_code": "+61",
  "currency": "AUD",
  "flag_emoji": "🇦🇺",
  "states": [
    {
      "id": 1,
      "name": "New South Wales",
      "state_code": "NSW",
      "cities": [...]
    }
  ]
}
```

---

### **Customer API** (`/api/customers/`)

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/` | GET | List customers | No |
| `/{id}/` | GET | Customer details | No |
| `/` | POST | Create customer | No |
| `/{id}/` | PUT/PATCH | Update customer | No |
| `/profile/update/` | POST | Update profile | No |
| `/addresses/create/` | POST | Create address | No |
| `/addresses/{id}/update/` | PUT/PATCH | Update address | No |
| `/addresses/{id}/delete/` | DELETE | Delete address | No |

**Create Address Request:**
```json
{
  "customer_id": "gid://shopify/Customer/123",
  "first_name": "John",
  "last_name": "Doe",
  "address1": "123 Main St",
  "city": "Sydney",
  "province": "NSW",
  "country": "Australia",
  "zip_code": "2000",
  "phone": "+61400000000",
  "is_default": false
}
```

---

### **Order API** (`/api/orders/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List orders |
| `/{id}/` | GET | Order details |
| `/customer-orders/?customer_email=x` | GET | Customer order history |
| `/{id}/update-address/` | POST | Update order address |
| `/{id}/cancel/` | POST | Cancel order |
| `/{id}/invoice/` | GET | Download invoice |
| `/recent/?limit=10` | GET | Recent orders |

**Customer Orders Response:**
```json
{
  "success": true,
  "orders": [...],
  "statistics": {
    "total_orders": 15,
    "pending_orders": 2,
    "fulfilled_orders": 13,
    "total_spent": 450.00
  }
}
```

---

### **Subscription API** (`/api/subscriptions/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/selling-plans/` | GET | List selling plans |
| `/checkout/create/` | POST | Create subscription checkout |
| `/{id}/` | GET | Subscription details |
| `/{id}/` | PATCH | Update subscription |
| `/{id}/pause/` | POST | Pause subscription |
| `/{id}/cancel/` | POST | Cancel subscription |

---

### **Skip API** (`/api/skips/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List skips |
| `/` | POST | Create skip request |
| `/{id}/` | GET | Skip details |
| `/{id}/confirm/` | POST | Confirm skip |
| `/{id}/cancel/` | POST | Cancel skip |
| `/policies/` | GET | Skip policies |
| `/analytics/` | GET | Skip analytics |

**Create Skip Request:**
```json
{
  "subscription_id": 123,
  "reason": "On vacation",
  "skip_type": "manual"
}
```

---

### **Product API** (`/api/products/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List products |
| `/{id}/` | GET | Product details |
| `/by-handle/{handle}/` | GET | Get by handle |
| `/featured/` | GET | Featured products |
| `/by-type/?type=x` | GET | Filter by type |
| `/search/?q=query` | GET | Search products |

---

### **Inventory API** (`/api/inventory/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List inventory levels |
| `/low-stock/?threshold=10` | GET | Low stock items |

---

## 💾 **DATABASE MODELS**

### **Entity Relationship Overview**

```
ShopifyCustomer (1) ─────< (N) ShopifyCustomerAddress
       │                              │
       │ (1)                          │
       │                              │
       ↓ (N)                          │
CustomerSubscription                  │
       │                              │
       │ (1)                          │
       │                              │
       ↓ (N)                          ↓
SubscriptionSkip           SubscriptionAddress
       │                              
       │ (1)                          
       │                              
       ↓ (N)                          
SkipNotification                      

ShopifyOrder (1) ─────< (N) ShopifyOrderLineItem
    │                            │
    │ (1)                        │ (1)
    │                            │
    ↓ (N)                        ↓
ShopifyOrderAddress      ShopifyProductVariant
                                 │
                                 │ (N)
                                 │
                                 ↓ (1)
                          ShopifyProduct
                                 │
                                 │ (1)
                                 │
                                 ├─< (N) ShopifyProductImage
                                 ├─< (N) ShopifyProductMetafield
                                 └─< (N) ShopifyInventoryItem
                                           │
                                           │ (N)
                                           │
                                           ↓ (1)
                                     ShopifyInventoryLevel
                                           │
                                           │ (N)
                                           │
                                           ↓ (1)
                                     ShopifyLocation
```

### **Key Model Fields Summary**

#### **Core Sync Fields** (Present in most models)
- `shopify_id` - Unique Shopify identifier
- `store_domain` - Multi-store support
- `created_at` / `updated_at` - Timestamps
- `last_synced` - Last sync timestamp
- `sync_status` - synced/pending/error

#### **Bidirectional Sync Fields**
- `needs_shopify_push` - Flag for pending push
- `shopify_push_error` - Last error message
- `last_pushed_to_shopify` - Push timestamp
- `created_in_django` - Origin flag
- `last_synced_from_shopify` - Pull timestamp

#### **Audit Fields**
- `created_by` / `updated_by` - User tracking
- `processed_by` - Admin action tracking
- `reason` / `notes` - Change reasons

---

## 🎯 **KEY FUNCTIONALITIES**

### **1. Subscription Box Management**

#### **Workflow**
1. **Product Setup**
   - Create selling plan (e.g., "Monthly Deluxe Box")
   - Set billing interval (monthly)
   - Configure delivery schedule
   - Set pricing (fixed or discount)
   - Associate products (book selections)

2. **Customer Subscribes**
   - Customer selects plan on Shopify
   - Checkout with subscription
   - Shopify creates SubscriptionContract
   - Webhook → Django creates CustomerSubscription

3. **Recurring Billing**
   - Shopify automatically bills on schedule
   - Success → Webhook → Create order
   - Failure → Webhook → Log billing attempt → Email customer

4. **Order Fulfillment**
   - Order created in Shopify
   - Webhook → Django syncs order
   - Admin processes fulfillment
   - Tracking info sent to customer

5. **Cutoff Management**
   - 14 days before: Reminder email
   - 7 days before: Cutoff notification
   - After cutoff: Order locked for processing

6. **Delivery & Renewal**
   - Order shipped
   - Next billing date calculated
   - Process repeats

---

### **2. Skip/Pause Functionality**

#### **Customer Skip Flow**
1. Customer logs in → Goes to Subscriptions tab
2. Clicks "Skip Next Delivery"
3. Modal opens:
   - Current delivery date shown
   - New delivery date calculated (next cycle)
   - Reason dropdown (vacation, too many books, etc.)
4. Customer confirms skip
5. AJAX POST to `/api/skips/`
6. Django:
   - Validates against policy (max skips, advance notice)
   - Creates SubscriptionSkip record (status: pending)
   - Updates CustomerSubscription (next_billing_date +1 cycle)
   - Sends confirmation email
7. Background sync:
   - Push updated dates to Shopify SubscriptionContract
8. Customer receives confirmation

#### **Skip Limits Enforcement**
- Max 4 skips per calendar year (configurable)
- Max 2 consecutive skips
- Must request 7 days before cutoff
- Skip fee optional (default: $0)

---

### **3. Address Management**

#### **Features**
- **Multiple Addresses**: Customer can save multiple addresses
- **Default Address**: One address marked as default
- **Subscription Address**: Separate primary address for subscriptions
- **Order Override**: One-time address change for single order

#### **Address Propagation Logic**
- **Change Subscription Address**:
  - Updates SubscriptionAddress model
  - Auto-propagates to all unshipped orders
  - Does NOT affect shipped orders
  - Syncs to Shopify subscription contract

- **Change Order Address**:
  - Creates OrderAddressOverride
  - Only affects that specific order
  - Marked as temporary or permanent
  - Does not change subscription address

---

### **4. Inventory Management**

#### **Real-time Sync**
- **Django → Shopify**:
  - Admin updates stock in Django
  - Model save() → `needs_shopify_push = True`
  - Background sync → GraphQL inventoryAdjustQuantities
  - Shopify stock updated

- **Shopify → Django**:
  - Stock changes in Shopify (manual or sales)
  - Webhook: inventory_levels/update
  - Django updates ShopifyInventoryLevel
  - No circular sync (skip_push_flag)

#### **Low Stock Alerts**
- `/api/inventory/low-stock/?threshold=10`
- Returns products with available ≤ threshold
- Used for reorder notifications

---

### **5. Multi-Currency Support**

#### **Supported Currencies** (10)
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- CAD (Canadian Dollar)
- AUD (Australian Dollar) - Default
- JPY (Japanese Yen)
- CNY (Chinese Yuan)
- CHF (Swiss Franc)
- SEK (Swedish Krona)
- NZD (New Zealand Dollar)

#### **Detection Methods**
1. Customer's IP geolocation
2. Browser locale
3. Shopify market assignment
4. Manual selection

#### **Currency Context Middleware**
```python
# locations/shopify_currency_service.py
class LocaleMiddleware:
    def __call__(self, request):
        # Detect currency from IP/locale
        currency = detect_currency(request)
        request.currency = currency
        return response
```

---

### **6. Email Automation**

#### **Triggered Emails**
- **Subscription**: Welcome, renewal reminder, payment failed, cancelled
- **Orders**: Confirmation, shipped, delivered
- **Skips**: Skip confirmed, cutoff reminder, limit warning
- **Account**: Password reset, email verification, MFA setup
- **Marketing**: Newsletter, promotions (opt-in)

#### **Email Templates**
- Stored in `email_manager/EmailTemplate`
- Variables: `{{ customer.first_name }}`, `{{ order.name }}`, etc.
- HTML & plain text versions
- Personalization support

---

### **7. Admin Dashboard** (Django Admin)

#### **Customizations** (Jazzmin)
- **Custom Branding**: Lavish Library logo & colors
- **Organized Sidebar**: Apps grouped logically
- **Icons**: Font Awesome icons for all models
- **Search**: Quick search across customers, orders, products
- **Filters**: Advanced filtering on all list views
- **Actions**: Bulk operations (sync, export, etc.)
- **Custom Views**: Analytics dashboards (planned)

#### **Admin Capabilities**
- Customer management (CRUD)
- Order processing & fulfillment
- Subscription management (pause, cancel, modify)
- Skip approvals & overrides
- Inventory adjustments
- Product management
- Sync operation monitoring
- Error log review
- Email template editing

---

## 🚀 **DEVELOPMENT & DEPLOYMENT**

### **Development Environment**

#### **Backend Setup**
```bash
# 1. Navigate to backend
cd app/lavish_backend

# 2. Activate virtual environment
# Windows:
.\lavish_backend_env\Scripts\activate
# macOS/Linux:
source lavish_backend_env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Populate location data
python manage.py populate_countries

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Start server
python manage.py runserver 8003
```

#### **Frontend Setup**
```bash
# 1. Navigate to frontend
cd app/lavish_frontend

# 2. Start Shopify dev server
shopify theme dev --store 7fa66c-ac.myshopify.com --port 9292
```

#### **Quick Start Scripts**
- **`START_BOTH_SERVERS.bat`** - Starts both backend & frontend
- **`START_SERVER_PORT_8003.bat`** - Backend only
- **`QUICK_START_UV.bat`** - UV package manager setup

---

### **Environment Variables**

Create `.env` in project root:
```env
# Shopify
SHOPIFY_STORE_URL=7fa66c-ac.myshopify.com
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_ACCESS_TOKEN=your_access_token
SHOPIFY_API_VERSION=2025-01

# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password

# Shipping (optional)
SENDAL_API_ENDPOINT=https://api.sendal.com/v1/rates
SENDAL_API_KEY=your_sendal_key

# Currency Exchange (optional)
EXCHANGE_RATE_API_KEY=your_exchange_rate_key
```

---

### **Production Deployment**

#### **Current Setup**
- **Frontend**: `viewing.endevops.net:9292` (Cloudflare Tunnel)
- **Backend**: `lavish-backend.endevops.net:8003` (Cloudflare Tunnel)

#### **Frontend (Shopify Theme)**
```bash
# 1. Test theme locally
shopify theme dev

# 2. Push to Shopify
shopify theme push --unpublished

# 3. Test on Shopify
# View unpublished theme URL in admin

# 4. Publish
shopify theme publish
```

#### **Backend (Django)**
```bash
# 1. Update settings for production
# - Set DEBUG = False
# - Update ALLOWED_HOSTS
# - Configure production database (PostgreSQL)
# - Set up static file serving
# - Configure email backend (SMTP)

# 2. Collect static files
python manage.py collectstatic

# 3. Run migrations
python manage.py migrate

# 4. Deploy to server
# - Use Gunicorn/uWSGI
# - Set up Nginx reverse proxy
# - Configure SSL (Let's Encrypt)
# - Set up systemd service
# - Configure Cloudflare Tunnel

# 5. Monitor & logs
# - Set up logging (Sentry, etc.)
# - Monitor performance (New Relic, etc.)
# - Database backups
```

---

### **CORS Configuration**

#### **Development**
```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = True  # For dev only
CORS_ALLOW_CREDENTIALS = True
```

#### **Production**
```python
CORS_ALLOWED_ORIGINS = [
    "https://7fa66c-ac.myshopify.com",
    "https://lavishlibrary.com.au",
    "https://www.lavishlibrary.com.au",
    "https://viewing.endevops.net",
    "https://lavish-backend.endevops.net",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Disable for security
```

---

### **Security Considerations**

#### **API Security**
- ✅ CORS properly configured for production
- ✅ CSRF tokens for state-changing operations
- ✅ HMAC signature verification for webhooks
- ✅ Rate limiting on API endpoints (planned)
- ❌ Authentication currently disabled (AllowAny)
  - **Recommendation**: Implement token-based auth for production

#### **Data Security**
- ✅ Sensitive data in environment variables
- ✅ HTTPS enforced for production
- ✅ Database connections encrypted (production)
- ✅ PII handling compliant
- ✅ Password hashing (Django default)

#### **Shopify Security**
- ✅ Access token securely stored
- ✅ Webhook signature verification
- ✅ Scoped API permissions
- ✅ Regular token rotation (manual)

---

## 📊 **PERFORMANCE CONSIDERATIONS**

### **Database Optimization**
- ✅ Indexes on frequently queried fields
- ✅ `select_related()` for foreign keys
- ✅ `prefetch_related()` for many-to-many
- ✅ Pagination for large querysets
- 📝 **Recommendation**: Migrate to PostgreSQL for production

### **API Performance**
- ✅ GraphQL pagination (cursor-based)
- ✅ Bulk operations for large datasets
- ✅ Rate limit tracking & throttling
- ✅ Retry logic with exponential backoff
- 📝 **Recommendation**: Implement caching (Redis)

### **Frontend Performance**
- ✅ Lazy loading for images
- ✅ Minified CSS/JS (Shopify handles)
- ✅ Responsive images
- ✅ Liquid variable caching
- 📝 **Recommendation**: Add service worker for offline support

---

## 🐛 **DEBUGGING & MONITORING**

### **Django Logging**
```python
# Configured in settings.py
LOGGING = {
    'handlers': {
        'file': {
            'filename': 'logs/django.log',
        },
        'console': {...},
    },
    'loggers': {
        'django': {'level': 'INFO'},
        'shopify_integration': {'level': 'DEBUG'},
    },
}
```

### **Log Files**
- `app/lavish_backend/logs/django.log` - All Django logs
- Console output - Real-time debugging

### **Sync Operation Monitoring**
- View in Django Admin: Shopify Integration → Sync Operations
- Shows progress, errors, timing
- Filter by status, date range

### **Browser Console**
- `django-integration.js` logs all API calls
- Error messages with emoji indicators (🌐 ✅ ❌)
- Request/response inspection

---

## 📝 **TESTING RECOMMENDATIONS**

### **Backend Tests**
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test customers
python manage.py test customer_subscriptions
```

### **Frontend Tests**
- Manual testing via Shopify CLI preview
- Test all tab navigations
- Test all modals & forms
- Test address cascading dropdowns
- Test responsive layouts

### **Integration Tests**
- Test full sync flow (Django ↔ Shopify)
- Test webhook handling
- Test API endpoint responses
- Test error handling & recovery

### **Load Testing**
- Simulate multiple concurrent users
- Test API rate limiting
- Test database query performance
- Benchmark sync operations

---

## 🎓 **LEARNING RESOURCES**

### **Shopify Development**
- [Shopify Theme Development Docs](https://shopify.dev/docs/themes)
- [Liquid Template Language](https://shopify.dev/docs/api/liquid)
- [Shopify Admin API](https://shopify.dev/docs/api/admin)
- [Subscription APIs](https://shopify.dev/docs/apps/selling-strategies/subscriptions)

### **Django Development**
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)

### **API Design**
- [REST API Best Practices](https://restfulapi.net/)
- [GraphQL Documentation](https://graphql.org/learn/)

---

## 🎯 **SUMMARY**

### **What You Have**
✅ **Comprehensive Subscription Management System**
✅ **Bidirectional Shopify ↔ Django Sync**
✅ **Enhanced Customer Account Portal**
✅ **Skip/Pause Functionality**
✅ **Multi-currency Support**
✅ **Real-time Inventory Management**
✅ **Location-based Services**
✅ **Email Automation**
✅ **Admin Dashboard**
✅ **Webhook Integration**
✅ **API-First Architecture**

### **Architecture Highlights**
- **Modular Design**: Separate Django apps for each domain
- **Scalable**: Ready for multi-store support
- **Extensible**: Easy to add new features
- **Maintainable**: Well-organized codebase
- **Production-Ready**: Deployment configuration included

### **Next Steps Recommendations**
1. **Security**: Implement API authentication for production
2. **Caching**: Add Redis for performance
3. **Testing**: Write comprehensive test suite
4. **Monitoring**: Set up Sentry/New Relic
5. **Documentation**: Keep this doc updated
6. **Backups**: Automate database backups
7. **CI/CD**: Set up GitHub Actions or similar
8. **Load Testing**: Stress test the system
9. **User Training**: Create admin user guides
10. **Analytics**: Implement business analytics dashboard

---

## 📞 **SUPPORT**

For questions or issues:
1. Check this documentation first
2. Review error logs (`logs/django.log`)
3. Check browser console for frontend issues
4. Review Shopify Admin logs
5. Contact development team

---

**Document Version**: 1.0  
**Last Updated**: December 12, 2025  
**Maintained By**: Development Team  
**Project**: Lavish Library Subscription Platform

