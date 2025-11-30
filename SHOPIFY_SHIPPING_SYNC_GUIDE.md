# Shopify Shipping Data Sync - Complete Guide

**Status:** ✅ Complete  
**Date:** November 30, 2025  
**Purpose:** Pull shipping carrier details, delivery profiles, zones, methods, and rates from Shopify

---

## 📦 What Was Built

### 1. **Shopify Shipping Sync Service** (`shipping/shopify_sync_service.py`)

**Purpose:** Sync all shipping-related data from Shopify API to Django database

**Key Features:**
- ✅ Sync carrier services (Sendal, custom carriers)
- ✅ Sync delivery profiles with zones and methods
- ✅ Query shipping rates for specific addresses
- ✅ Get detailed carrier service information
- ✅ Full error handling and logging
- ✅ Sync operation tracking

**Key Methods:**
```python
# Sync everything
service.sync_all_shipping_data()

# Sync only carrier services
service.sync_carrier_services()

# Sync only delivery profiles (includes zones & methods)
service.sync_delivery_profiles()

# Get rates for an address
service.get_shipping_rates_for_address(origin, destination, items)

# Get carrier details
service.get_carrier_service_details(carrier_id)
```

### 2. **Management Command** (`shipping/management/commands/sync_shipping_data.py`)

**Purpose:** CLI tool to sync shipping data

**Usage:**
```bash
# Sync everything
python manage.py sync_shipping_data

# Sync only carrier services
python manage.py sync_shipping_data --carrier-services

# Sync only delivery profiles
python manage.py sync_shipping_data --delivery-profiles

# Show detailed information after sync
python manage.py sync_shipping_data --show-details

# Get details for specific carrier
python manage.py sync_shipping_data --carrier-id 12345
```

### 3. **REST API Endpoints** (`shipping/views.py`)

**New Endpoints:**

1. **GET `/api/shipping/carriers/`** - List all carrier services
2. **GET `/api/shipping/delivery-profiles/`** - List delivery profiles with zones/methods
3. **POST `/api/shipping/sync/`** - Trigger shipping data sync
4. **GET `/api/shipping/rates/?country=US&postal_code=10001`** - Query available rates
5. **POST `/api/shipping/calculate-rates/`** - Shopify callback (existing)
6. **POST `/api/shipping/test-rates/`** - Test endpoint (existing)

---

## 🚀 Quick Start

### Step 1: Sync Shipping Data from Shopify

```bash
cd app/lavish_backend
python manage.py sync_shipping_data --show-details
```

**Expected Output:**
```
================================================================================
SHOPIFY SHIPPING DATA SYNC
================================================================================

Syncing carrier services...

Carrier Services:
  - Synced: 2
  - Created: 1
  - Updated: 1
  - No errors

Syncing delivery profiles...

Delivery Profiles:
  - Profiles: 3
  - Zones: 8
  - Methods: 15
  - No errors

================================================================================
SYNC SUMMARY
================================================================================
Carrier Services: 2 synced (1 created, 1 updated)
Delivery Profiles: 3 profiles, 8 zones, 15 methods
✓ Sync completed successfully with no errors

================================================================================
SYNCED DATA DETAILS
================================================================================

Carrier Services:
  • Lavish Shipping [✓ Active]
    ID: 123456
    Type: api
    Callback: https://lavish-backend.endevops.net/api/shipping/calculate-rates/
    Service Discovery: True

Delivery Profiles:
  • General Shipping [DEFAULT]
    ID: 789012
    Zones: 3
      - Domestic US: US
        Methods: 3
          • Standard Shipping (shipping)
          • Express Shipping (shipping)
          • Overnight Shipping (shipping)
      - Canada: CA
        Methods: 2
          • Standard Shipping (shipping)
          • Express Shipping (shipping)
      - International: GB, AU, FR, DE, ES +45 more
        Methods: 1
          • International Shipping (shipping)
```

### Step 2: Query Synced Data via API

```bash
# List carrier services
curl -X GET http://localhost:8003/api/shipping/carriers/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# List delivery profiles
curl -X GET http://localhost:8003/api/shipping/delivery-profiles/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Query rates for US address
curl -X GET "http://localhost:8003/api/shipping/rates/?country=US&postal_code=10001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: Trigger Sync via API

```bash
# Sync all shipping data
curl -X POST http://localhost:8003/api/shipping/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "all"}'

# Sync only carrier services
curl -X POST http://localhost:8003/api/shipping/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "carrier_services"}'
```

---

## 📊 Database Models

### ShopifyCarrierService
Stores Shopify carrier services (Sendal, custom carriers)

**Fields:**
- `shopify_id` - Unique Shopify ID
- `name` - Carrier service name
- `active` - Whether active
- `service_discovery` - Auto-discover rates
- `carrier_service_type` - 'api' or 'legacy'
- `callback_url` - Rate calculation callback URL
- `format` - 'json' or 'xml'
- `store_domain` - Shopify store domain

### ShopifyDeliveryProfile
Stores delivery profiles (shipping configurations)

**Fields:**
- `shopify_id` - Unique Shopify ID
- `name` - Profile name
- `active` - Whether active
- `default` - Whether default profile
- `locations_without_rates_to_ship` - JSON array
- `store_domain` - Shopify store domain

### ShopifyDeliveryZone
Stores shipping zones (geographic regions)

**Fields:**
- `profile` - FK to DeliveryProfile
- `shopify_id` - Unique Shopify ID
- `name` - Zone name (e.g., "Domestic US", "Canada", "International")
- `countries` - JSON array of country codes and names
- `store_domain` - Shopify store domain

### ShopifyDeliveryMethod
Stores shipping methods (rate options)

**Fields:**
- `zone` - FK to DeliveryZone
- `shopify_id` - Unique Shopify ID
- `name` - Method name (e.g., "Standard Shipping")
- `method_type` - 'shipping' or 'pickup'
- `min_delivery_date_time` - Earliest delivery
- `max_delivery_date_time` - Latest delivery
- `store_domain` - Shopify store domain

### ShippingSyncLog
Tracks sync operations

**Fields:**
- `operation_type` - 'bulk_import', 'single_update', 'webhook_update'
- `carriers_processed` - Count
- `profiles_processed` - Count
- `zones_processed` - Count
- `methods_processed` - Count
- `errors_count` - Count
- `started_at` - Timestamp
- `completed_at` - Timestamp
- `status` - 'running', 'completed', 'failed'
- `error_details` - JSON error log

---

## 🔍 API Details

### GET `/api/shipping/carriers/`

**Response:**
```json
{
  "carrier_services": [
    {
      "id": 1,
      "shopify_id": "123456",
      "name": "Lavish Shipping",
      "callback_url": "https://lavish-backend.endevops.net/api/shipping/calculate-rates/",
      "service_discovery": true,
      "carrier_service_type": "api",
      "format": "json",
      "active": true
    }
  ]
}
```

### GET `/api/shipping/delivery-profiles/`

**Response:**
```json
{
  "delivery_profiles": [
    {
      "id": 1,
      "shopify_id": "789012",
      "name": "General Shipping",
      "default": true,
      "zones": [
        {
          "id": 1,
          "shopify_id": "111222",
          "name": "Domestic US",
          "countries": [
            {"country_code": "US", "province_code": null, "name": "United States"}
          ],
          "methods": [
            {
              "id": 1,
              "shopify_id": "333444",
              "name": "Standard Shipping",
              "method_type": "shipping"
            },
            {
              "id": 2,
              "shopify_id": "333445",
              "name": "Express Shipping",
              "method_type": "shipping"
            }
          ]
        }
      ]
    }
  ]
}
```

### GET `/api/shipping/rates/?country=US&postal_code=10001`

**Response:**
```json
{
  "success": true,
  "country": "US",
  "postal_code": "10001",
  "available_rates": [
    {
      "service_name": "Standard Shipping",
      "service_code": "333444",
      "zone": "Domestic US",
      "profile": "General Shipping",
      "method_type": "shipping"
    },
    {
      "service_name": "Express Shipping",
      "service_code": "333445",
      "zone": "Domestic US",
      "profile": "General Shipping",
      "method_type": "shipping"
    }
  ],
  "count": 2
}
```

### POST `/api/shipping/sync/`

**Request:**
```json
{
  "sync_type": "all"
}
```

**Options for sync_type:**
- `"all"` - Sync everything
- `"carrier_services"` - Only carrier services
- `"delivery_profiles"` - Only delivery profiles (includes zones & methods)

**Response:**
```json
{
  "success": true,
  "sync_type": "all",
  "results": {
    "carrier_services": 2,
    "delivery_profiles": 3,
    "delivery_zones": 8,
    "delivery_methods": 15,
    "errors": []
  }
}
```

---

## 🔧 How It Works

### Carrier Services Sync

**API Used:** Shopify REST API  
**Endpoint:** `/admin/api/2024-10/carrier_services.json`

**What It Pulls:**
- Carrier service ID
- Name (e.g., "Lavish Shipping", "Sendal")
- Active status
- Service discovery enabled/disabled
- Callback URL for rate calculation
- Format (JSON/XML)

**Use Case:** Know which carrier services are configured in Shopify, including your custom carrier service for Sendal integration.

### Delivery Profiles Sync

**API Used:** Shopify GraphQL API  
**Query:** `deliveryProfiles`

**What It Pulls:**
- Delivery profile (shipping configuration)
- Delivery zones (geographic regions)
- Countries per zone
- Delivery methods per zone (rate options)
- Rate provider information (if fixed rates)

**Use Case:** Understand your complete shipping setup - which zones cover which countries, what shipping methods are available per zone.

### Rate Querying

**How:** Query synced data in Django database  
**Input:** Country code, postal code (optional)  
**Output:** List of available shipping methods for that location

**Use Case:** Quickly check which shipping options are available for a customer's location without hitting Shopify API every time.

---

## 📝 Usage Examples

### Python/Django Shell

```python
from shipping.shopify_sync_service import ShopifyShippingSyncService
from shipping.models import ShopifyCarrierService, ShopifyDeliveryProfile

# Initialize service
service = ShopifyShippingSyncService()

# Sync all data
results = service.sync_all_shipping_data()
print(f"Synced: {results}")

# Query carrier services
carriers = ShopifyCarrierService.objects.filter(active=True)
for carrier in carriers:
    print(f"{carrier.name}: {carrier.callback_url}")

# Query delivery profiles
profiles = ShopifyDeliveryProfile.objects.all()
for profile in profiles:
    print(f"\nProfile: {profile.name}")
    for zone in profile.zones.all():
        countries = ', '.join([c['country_code'] for c in zone.countries])
        print(f"  Zone: {zone.name} ({countries})")
        for method in zone.methods.all():
            print(f"    - {method.name}")

# Get rates for US address
rates = service.get_shipping_rates_for_address(
    origin={'country': 'US', 'postal_code': '10001'},
    destination={'country': 'US', 'postal_code': '90210'},
    items=[{'grams': 1000, 'price': 2999}]
)
print(f"Available rates: {rates}")
```

### Management Command

```bash
# Full sync with details
python manage.py sync_shipping_data --show-details

# Quick sync (no details)
python manage.py sync_shipping_data

# Sync only carriers
python manage.py sync_shipping_data --carrier-services

# Sync only profiles
python manage.py sync_shipping_data --delivery-profiles

# Get specific carrier details
python manage.py sync_shipping_data --carrier-id 123456
```

### REST API

```bash
# Sync all data
curl -X POST http://localhost:8003/api/shipping/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "all"}'

# List carriers
curl http://localhost:8003/api/shipping/carriers/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# List profiles with zones and methods
curl http://localhost:8003/api/shipping/delivery-profiles/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Query rates for UK
curl "http://localhost:8003/api/shipping/rates/?country=GB&postal_code=SW1A%201AA" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 Benefits

### 1. **Visibility**
- See exactly what carrier services are configured
- Understand your complete shipping zone setup
- Know which methods are available per country

### 2. **Performance**
- Query shipping options from local database (fast)
- No need to hit Shopify API for every rate query
- Cached data with periodic sync

### 3. **Integration**
- Verify Sendal carrier service is registered
- Check callback URLs are correct
- Ensure service discovery is enabled

### 4. **Debugging**
- View complete shipping configuration
- Track sync operations and errors
- Detailed logging for troubleshooting

---

## 🔄 Recommended Workflow

1. **Initial Setup** (once)
   ```bash
   python manage.py sync_shipping_data --show-details
   ```
   This pulls all existing Shopify shipping configuration into your Django database.

2. **Regular Updates** (daily/weekly)
   ```bash
   python manage.py sync_shipping_data
   ```
   Keep your local data in sync with Shopify changes.

3. **On-Demand Queries** (anytime)
   ```bash
   curl "http://localhost:8003/api/shipping/rates/?country=US"
   ```
   Query available shipping options without API calls.

4. **After Changes** (when you modify Shopify shipping settings)
   ```bash
   python manage.py sync_shipping_data --show-details
   ```
   Re-sync to see your changes reflected.

---

## ⚠️ Important Notes

1. **Authentication Required**
   - All API endpoints require authentication
   - Except `/api/shipping/calculate-rates/` (Shopify webhook)

2. **Shopify API Limits**
   - Rate limited by Shopify
   - Service handles retries automatically
   - Uses GraphQL for efficiency

3. **Data Freshness**
   - Synced data is snapshot from Shopify
   - Re-sync to get latest changes
   - Consider scheduled sync (cron/celery)

4. **Carrier Service Callback**
   - `/api/shipping/calculate-rates/` is for Shopify callbacks
   - Used during checkout for live rate calculation
   - Different from synced data (which is configuration)

---

## 📚 Related Documentation

- `SHIPPING_CURRENCY_INTEGRATION_COMPLETE.md` - Full shipping integration guide
- `QUICKSTART_SHIPPING.md` - Quick setup guide
- Shopify Carrier Service API: https://shopify.dev/docs/api/admin-rest/2024-10/resources/carrierservice
- Shopify Delivery Profiles: https://shopify.dev/docs/api/admin-graphql/2024-10/objects/DeliveryProfile

---

**Status:** ✅ Ready to use  
**Testing:** Run `python manage.py sync_shipping_data --show-details`  
**Next Steps:** Schedule regular syncs to keep data current
