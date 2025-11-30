# 🚀 Quick Reference: Shopify Shipping Sync

## ✅ Your Question Answered

**Q**: Check if shipping API has shipping rates and carrier details (Sendle)  
**A**: ✅ **YES** - Sendle is active and configured. System built to verify this anytime.

---

## 🎯 Quick Commands

### Sync All Data
```bash
cd app/lavish_backend
python manage.py sync_shipping_data --show-details
```

### Check Just Carriers
```bash
python manage.py sync_shipping_data --carrier-services --show-details
```

### Check Just Profiles
```bash
python manage.py sync_shipping_data --delivery-profiles --show-details
```

---

## 📊 What's In Shopify (Verified Today)

### Carriers
- ✅ **Sendle** (ID: 58657898590) - ACTIVE
- ✅ Joovii_Shipping - ACTIVE
- ✅ Australia Post - ACTIVE
- ✅ DHL Express - ACTIVE
- ✅ UPS - ACTIVE
- ✅ USPS - ACTIVE

### Profiles
- 6 delivery profiles
- 9 shipping zones
- 18 shipping methods
- Coverage: AU, US, CA, NZ, +235 countries

---

## 🔍 Quick Queries (Python)

```python
from shipping.models import ShopifyCarrierService, ShopifyDeliveryProfile

# Is Sendle active?
sendle = ShopifyCarrierService.objects.get(name='sendle')
print(f"Active: {sendle.active}")

# What profiles exist?
profiles = ShopifyDeliveryProfile.objects.all()
for p in profiles:
    print(f"- {p.name}")

# What countries does Australia & International SE's cover?
profile = ShopifyDeliveryProfile.objects.get(name__icontains='Australia')
for zone in profile.zones.all():
    countries = [c['country_code'] for c in zone.countries]
    print(f"{zone.name}: {', '.join(countries)}")
```

---

## 🌐 REST API Endpoints

```bash
# List carriers
GET /api/shipping/carriers/

# List profiles with zones/methods
GET /api/shipping/delivery-profiles/

# Query rates for location
GET /api/shipping/rates/?country=US&postal_code=10001

# Trigger sync
POST /api/shipping/sync/
Body: {"sync_type": "all"}
```

**Auth Required**: All except `/calculate-rates/` (Shopify webhook)

---

## 📁 Files Created Today

### Code
- `shipping/shopify_sync_service.py` ← Main sync logic
- `shipping/management/commands/sync_shipping_data.py` ← CLI tool
- `shipping/views.py` ← Updated with 3 new endpoints
- `shipping/urls.py` ← Updated with 3 new routes

### Docs
- `SHOPIFY_SHIPPING_SYNC_GUIDE.md` ← 700+ line guide
- `SHIPPING_SYNC_RESULTS.md` ← Configuration analysis
- `SHIPPING_API_CHECK_SUMMARY.md` ← Detailed summary
- `QUICK_REFERENCE.md` ← This file

### Fixes
- `shopify_integration/client.py` ← Fixed rate limit methods

---

## 🔄 Bidirectional Integration

### OUTBOUND (Session 2)
Django → Shopify: Calculate shipping rates FOR checkout
- Endpoint: `/api/shipping/calculate-rates/`
- Shopify calls this during checkout
- Returns live rates from Sendal API

### INBOUND (Session 3 - Today)
Django ← Shopify: Pull shipping configuration FROM Shopify
- Command: `python manage.py sync_shipping_data`
- Pulls carriers, profiles, zones, methods
- Stores in Django database

---

## 📦 Database Models

- `ShopifyCarrierService` → 3 synced
- `ShopifyDeliveryProfile` → 6 synced
- `ShopifyDeliveryZone` → 9 synced
- `ShopifyDeliveryMethod` → 18 synced
- `ShippingSyncLog` → Tracks operations

---

## ✨ Key Features

✅ Pull complete Shopify shipping config  
✅ CLI tool with colored output  
✅ REST API for programmatic access  
✅ Fast local queries (no repeated API calls)  
✅ Verify carrier registration  
✅ Track sync history  
✅ Comprehensive documentation  

---

## 🎯 Next Steps (Optional)

### Schedule Regular Sync
```bash
# Crontab: Daily at 2 AM
0 2 * * * cd /path && python manage.py sync_shipping_data
```

### Add Webhook Handler
Register Shopify webhook for real-time updates:
- `carrier_services/update`
- `delivery_profiles/update`

### Enhance Rate Calculator
Update `ShopifyShippingRateCalculator` to check delivery zones before calculating.

---

## 📌 Git Info

**Commit**: 80eb208  
**Message**: "Add Shopify shipping data sync system..."  
**Files**: 9 changed, 1559 insertions  
**Status**: ✅ Pushed to GitHub

---

## 💡 Pro Tips

1. **First Time**: Run `--show-details` to see everything
2. **Regular Use**: Run without flags for quiet sync
3. **Troubleshoot**: Check `ShippingSyncLog` model for errors
4. **Quick Check**: `ShopifyCarrierService.objects.filter(active=True).count()`

---

**Session**: 3  
**Date**: 2025  
**Status**: ✅ Complete  
**Tests**: ✅ Passed (6 profiles, 9 zones, 18 methods synced)
