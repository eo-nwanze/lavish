# Quick Reference - Shopify Sync Commands

## ✅ All Issues Fixed!

### 1. Email Logo Display
**Status**: ✅ Fixed  
**Solution**: Static files collected  
```bash
python manage.py collectstatic --noinput
```

### 2. Customer Address Sync  
**Status**: ✅ Fixed  
**How it works**: Addresses auto-flag when edited, then push with command  
```bash
# Push all pending addresses to Shopify
python manage.py push_pending_to_shopify --addresses-only
```

### 3. Inventory Tracking
**Status**: ✅ Fixed  
**Solution**: Inventory tracking enabled for all products  
```bash
# Fix any products missing inventory tracking
python fix_inventory_tracking.py
```

---

## Daily Workflow

### When editing customer addresses in Django:
1. Edit address in Django admin
2. Run: `python manage.py push_pending_to_shopify --addresses-only`
3. ✅ Address synced to Shopify

### When updating inventory in Django:
1. Edit inventory level in Django admin  
2. Run: `python manage.py push_pending_to_shopify --inventory-only`
3. ✅ Inventory synced to Shopify

### Sync everything at once:
```bash
python manage.py push_pending_to_shopify
```

---

## Verification Commands

### Check if address needs syncing:
```python
python manage.py shell
>>> from customers.models import ShopifyCustomerAddress
>>> pending = ShopifyCustomerAddress.objects.filter(needs_shopify_push=True)
>>> print(f"{pending.count()} addresses need syncing")
```

### Check if inventory needs syncing:
```python
python manage.py shell
>>> from inventory.models import ShopifyInventoryLevel
>>> pending = ShopifyInventoryLevel.objects.filter(needs_shopify_push=True)
>>> print(f"{pending.count()} inventory levels need syncing")
```

---

## Test Product Status

**Product**: Test Product from Django 2025-11-29 14:24  
**Shopify ID**: gid://shopify/Product/7507886080094  
**Inventory Item**: gid://shopify/InventoryItem/44346220609630  
**Tracking**: ✅ ENABLED  
**Stock**: 0 units (ready to be updated)

---

## Important Notes

✅ **No code was destroyed** - All existing sync logic preserved  
✅ **Models auto-detect changes** - `needs_shopify_push` flag set automatically  
✅ **Bidirectional sync working** - Both Django→Shopify and Shopify→Django  

📝 **Recommendation**: Set up a cron job to auto-sync every 15 minutes:
```bash
*/15 * * * * cd /path/to/project && python manage.py push_pending_to_shopify
```

---

See `SHOPIFY_SYNC_FIXES.md` for detailed technical documentation.
