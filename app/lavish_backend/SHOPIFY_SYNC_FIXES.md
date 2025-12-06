# FIXES APPLIED - December 7, 2025

## Issues Fixed

### 1. ✅ Email Logo Not Showing
**Problem**: Logo wasn't displaying in email templates  
**Root Cause**: Static files not collected  
**Solution**: Ran `python manage.py collectstatic --noinput`  
**Result**: Logo now accessible at `/static/img/Lavish-logo.png` for all email templates

---

### 2. ✅ Customer Address Updates Not Syncing to Shopify
**Problem**: Test User's address changes in Django weren't pushing to Shopify  
**Root Cause**: Address model has auto-detection via `save()` method but needed manual trigger  
**Solution**: Created management command to push pending changes

**How It Works**:
- `ShopifyCustomerAddress` model has `needs_shopify_push` flag
- When address is edited in Django, `save()` method automatically sets flag to `True`
- Run command to push pending addresses:
  ```bash
  python manage.py push_pending_to_shopify --addresses-only
  ```

**Files Created**:
- `customers/management/commands/push_pending_to_shopify.py` - Management command to sync pending changes

**Automatic Sync**:
The address model (lines 162-185 in `customers/models.py`) automatically detects changes:
```python
def save(self, *args, **kwargs):
    """Auto-track changes for bidirectional sync"""
    skip_push_flag = kwargs.pop('skip_push_flag', False)
    
    if self.pk and not skip_push_flag:
        # Check if address changed
        try:
            old = ShopifyCustomerAddress.objects.get(pk=self.pk)
            # Check if any address field changed
            if (old.address1 != self.address1 or old.address2 != self.address2 or
                old.city != self.city or old.province != self.province or
                old.country != self.country or old.zip_code != self.zip_code or
                old.phone != self.phone or old.is_default != self.is_default or
                old.first_name != self.first_name or old.last_name != self.last_name or
                old.company != self.company):
                self.needs_shopify_push = True
        except ShopifyCustomerAddress.DoesNotExist:
            pass
```

**Usage**:
1. Edit address in Django admin or form
2. Run: `python manage.py push_pending_to_shopify --addresses-only`
3. Address syncs to Shopify via REST API

---

### 3. ✅ Products Show "Inventory Not Tracked" in Shopify
**Problem**: Test Product created in Django appeared on Shopify but showed "Inventory not tracked"  
**Root Cause**: 
- Product variants didn't have `inventory_item` linked
- Inventory tracking not enabled in Shopify

**Solution**: Created script to:
1. Fetch inventory item data from Shopify for each variant
2. Link inventory items to variants in Django
3. Enable inventory tracking via GraphQL mutation
4. Sync inventory levels from Shopify

**Files Created**:
- `fix_inventory_tracking.py` - Script to enable tracking for all products
- `check_test_product_inventory.py` - Diagnostic script

**Results**:
```
[Product] Test Product from Django 2025-11-29 14:24
   [SUCCESS] Updated inventory item: gid://shopify/InventoryItem/44346220609630
      Tracked: False
   [Enabling] inventory tracking...
   [SUCCESS] Tracking enabled!
      • 8 Mellifont Street: 0 units
```

**How to Use**:
```bash
# Fix all products with missing inventory tracking
python fix_inventory_tracking.py

# Check specific product's inventory status
python check_test_product_inventory.py
```

---

## Commands Reference

### Push Pending Shopify Changes
```bash
# Push all pending changes (addresses + inventory)
python manage.py push_pending_to_shopify

# Push only addresses
python manage.py push_pending_to_shopify --addresses-only

# Push only inventory
python manage.py push_pending_to_shopify --inventory-only
```

### Fix Inventory Tracking
```bash
# Enable tracking for products created in Django
python fix_inventory_tracking.py
```

### Check Product Inventory
```bash
# Diagnostic check for test products
python check_test_product_inventory.py
```

### Collect Static Files
```bash
# Make static files available for email templates
python manage.py collectstatic --noinput
```

---

## How Bidirectional Sync Works

### Customer Addresses
**Django → Shopify** (Push):
1. Edit address in Django (admin or form)
2. Model's `save()` method detects changes
3. Sets `needs_shopify_push = True`
4. Run `push_pending_to_shopify` command
5. Uses `address_bidirectional_sync_fixed.py` REST API integration
6. Updates address in Shopify

**Shopify → Django** (Pull):
- Webhooks handle real-time updates
- Manual sync via admin dashboard

### Inventory
**Django → Shopify** (Push):
1. Update inventory level in Django
2. Model's `save()` method detects changes (in `inventory/models.py`)
3. Sets `needs_shopify_push = True`
4. Run `push_pending_to_shopify` command
5. Uses GraphQL `inventoryAdjustQuantities` mutation
6. Updates inventory in Shopify

**Shopify → Django** (Pull):
- Real-time sync service
- Manual sync via admin dashboard

---

## Technical Details

### Address Sync Service
**File**: `customers/address_bidirectional_sync_fixed.py`
**Method**: REST API (GraphQL deprecated for addresses)
**Endpoint**: `/admin/api/2024-10/customers/{customer_id}/addresses.json`

### Inventory Sync Service  
**File**: `inventory/bidirectional_sync.py`
**Method**: GraphQL Admin API
**Mutations**:
- `inventoryItemUpdate` - Enable tracking
- `inventoryAdjustQuantities` - Update quantities

### Models with Auto-Sync
1. **ShopifyCustomerAddress** (`customers/models.py`)
   - Auto-detects address changes
   - Sets `needs_shopify_push` flag

2. **ShopifyInventoryLevel** (`inventory/models.py`)
   - Auto-detects quantity changes
   - Sets `needs_shopify_push` flag

---

## Testing

### Verify Address Sync
```python
from customers.models import ShopifyCustomerAddress
from customers.address_bidirectional_sync_fixed import push_address_to_shopify

# Find Test User's address
address = ShopifyCustomerAddress.objects.filter(
    customer__email='testuser2@example.com'
).first()

# Check if needs push
print(f"Needs push: {address.needs_shopify_push}")

# Manually push
result = push_address_to_shopify(address)
print(result)
```

### Verify Inventory Tracking
```python
from products.models import ShopifyProduct

# Check Test Product
product = ShopifyProduct.objects.filter(
    title__icontains='Test Product from Django'
).first()

variant = product.variants.first()
inv_item = variant.inventory_item

print(f"Inventory Item ID: {inv_item.shopify_id}")
print(f"Tracked: {inv_item.tracked}")
print(f"Stock: {inv_item.levels.first().available}")
```

---

## Next Steps

1. **Set Initial Inventory**: Products now tracked but have 0 stock - update in Shopify or Django
2. **Test Address Forms**: Test address editing in customer portal
3. **Monitor Sync**: Check Django admin for `needs_shopify_push` flags
4. **Schedule Sync**: Consider cron job for automatic pending syncs:
   ```bash
   # Add to crontab
   */15 * * * * cd /path/to/project && python manage.py push_pending_to_shopify
   ```

---

## Files Modified/Created

### Created:
- `customers/management/commands/push_pending_to_shopify.py`
- `fix_inventory_tracking.py`
- `check_test_product_inventory.py`
- `SHOPIFY_SYNC_FIXES.md` (this file)

### Existing (No Changes):
- `customers/models.py` - Already has auto-detection
- `customers/address_bidirectional_sync_fixed.py` - Already working
- `inventory/bidirectional_sync.py` - Already working
- `inventory/models.py` - Already has auto-detection

---

## Summary

✅ **All 3 issues resolved**:
1. Email logo now displays (static files collected)
2. Address changes auto-flag for sync + command created
3. Inventory tracking enabled for all products

**No code was destroyed** - All existing bidirectional sync logic preserved and working correctly.
