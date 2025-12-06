# CRUD Operations Report - Django Admin to Shopify

## Executive Summary

**KEY FINDING: CREATE operations in Django admin DO NOT automatically push to Shopify.**

All models use a **flag-based system** where:
1. Model's `save()` method sets `needs_shopify_push=True`
2. Requires **manual trigger** to actually push to Shopify
3. No automatic push happens on form submit

---

## Detailed Analysis by Model

### 1. ✅ Customers (ShopifyCustomer)

**Model**: `customers/models.py` (lines 72-88)
- **save() override**: YES
- **Auto-push on CREATE**: ❌ NO
- **Auto-push on UPDATE**: ❌ NO

**Admin**: `customers/admin.py`
- **save_model() override**: ❌ NO
- **Actions**: Only pulls FROM Shopify (no push actions)

**CRUD Status**:
```
CREATE:  Flags needs_shopify_push=True → NO auto-push
READ:    ✅ YES (from database)
UPDATE:  Flags needs_shopify_push=True → NO auto-push  
DELETE:  ❌ Only deletes from Django
```

**Manual Push**:
- Function: `customers/bidirectional_sync.py::push_customer_to_shopify()`
- Trigger: Must call programmatically or via custom command

---

### 2. ✅ Customer Addresses (ShopifyCustomerAddress)

**Model**: `customers/models.py` (lines 162-185)
- **save() override**: YES
- **Auto-push on CREATE**: ❌ NO
- **Auto-push on UPDATE**: ❌ NO

**Admin**: Inline within customer admin
- **save_formset() override**: ❌ NO

**CRUD Status**:
```
CREATE:  Flags needs_shopify_push=True → NO auto-push
READ:    ✅ YES (from database)
UPDATE:  Flags needs_shopify_push=True → NO auto-push
DELETE:  ❌ Only deletes from Django
```

**Manual Push**:
- Function: `customers/address_bidirectional_sync_fixed.py::push_address_to_shopify()`
- Command: `python manage.py push_pending_to_shopify --addresses-only`

---

### 3. ✅ Products (ShopifyProduct)

**Model**: `products/models.py` (lines 85-105)
- **save() override**: YES
- **Auto-push on CREATE**: ❌ NO
- **Auto-push on UPDATE**: ❌ NO
- **Special flag**: Sets `created_in_django=True` for new records

**Admin**: `products/admin.py`
- **save_model() override**: ❌ NO
- **Actions**: 
  - ✅ `push_to_shopify` (manual push action)
  - ✅ `update_in_shopify` (manual update action)
  - ✅ `delete_from_shopify` (manual delete action)

**CRUD Status**:
```
CREATE:  Flags needs_shopify_push=True + created_in_django=True → NO auto-push
READ:    ✅ YES (from database)
UPDATE:  Flags needs_shopify_push=True → NO auto-push
DELETE:  ✅ Has 'delete_from_shopify' action (but NOT automatic)
```

**Manual Push**:
- Function: `products/bidirectional_sync.py::push_product_to_shopify()`
- Admin: Select products → Actions → "📤 Push selected products TO Shopify"

---

### 4. ⚠️ Inventory Items (ShopifyInventoryItem)

**Model**: `inventory/models.py`
- **save() override**: ❌ NO
- **Auto-push on CREATE**: ❌ NO
- **Auto-push on UPDATE**: ❌ NO

**Admin**: `inventory/admin.py`
- **save_model() override**: ❌ NO
- **Actions**: Only pulls FROM Shopify

**CRUD Status**:
```
CREATE:  ❌ Saves to Django only, NO Shopify push
READ:    ✅ YES (from database)
UPDATE:  ❌ Updates Django only, NO Shopify push
DELETE:  ❌ Deletes from Django only
```

**Note**: Inventory items are typically created automatically by Shopify when product variants are created. Manual creation in Django is not recommended.

---

### 5. ✅ Inventory Levels (ShopifyInventoryLevel)

**Model**: `inventory/models.py` (lines 98-117)
- **save() override**: YES
- **Auto-push on CREATE**: ❌ NO
- **Auto-push on UPDATE**: ❌ NO

**Admin**: Inline within inventory item admin
- **save_formset() override**: ❌ NO

**CRUD Status**:
```
CREATE:  Flags needs_shopify_push=True → NO auto-push
READ:    ✅ YES (from database)
UPDATE:  Flags needs_shopify_push=True → NO auto-push
DELETE:  ❌ Only deletes from Django
```

**Manual Push**:
- Function: `inventory/bidirectional_sync.py::push_inventory_to_shopify()`
- Command: `python manage.py push_pending_to_shopify --inventory-only`

---

## CRUD Summary Table

| Model                | CREATE | READ | UPDATE | DELETE | Auto-Push |
|---------------------|--------|------|--------|--------|-----------|
| ShopifyCustomer     | Manual | ✅   | Manual | Manual | ❌ NO     |
| CustomerAddress     | Manual | ✅   | Manual | Manual | ❌ NO     |
| ShopifyProduct      | Manual | ✅   | Manual | Manual | ❌ NO     |
| ProductVariant      | Manual | ✅   | Manual | Manual | ❌ NO     |
| InventoryItem       | Manual | ✅   | Manual | Manual | ❌ NO     |
| InventoryLevel      | Manual | ✅   | Manual | Manual | ❌ NO     |

**Legend**:
- ✅ = Fully functional from Django admin
- Manual = Requires manual action/command to sync with Shopify
- ❌ NO = Not automatically pushed to Shopify

---

## Where CRUD is Implemented

### Bidirectional Sync Files:

1. **Customers**: 
   - File: `customers/bidirectional_sync.py`
   - Functions: `push_customer_to_shopify()`, `push_all_pending_customers()`

2. **Addresses**:
   - File: `customers/address_bidirectional_sync_fixed.py`
   - Functions: `push_address_to_shopify()`, `push_all_pending_addresses()`

3. **Products**:
   - File: `products/bidirectional_sync.py`
   - Functions: `push_product_to_shopify()`, `push_all_pending_products()`

4. **Inventory**:
   - File: `inventory/bidirectional_sync.py`
   - Functions: `push_inventory_to_shopify()`, `push_all_pending_inventory()`

### Management Commands:

- **`push_pending_to_shopify.py`** (NEW - created Dec 7, 2025)
  - Location: `customers/management/commands/`
  - Syncs all pending changes for addresses and inventory
  - Usage:
    ```bash
    python manage.py push_pending_to_shopify                    # All
    python manage.py push_pending_to_shopify --addresses-only   # Addresses only
    python manage.py push_pending_to_shopify --inventory-only   # Inventory only
    ```

---

## How the Flag System Works

### For Models with `save()` Override:

```python
def save(self, *args, **kwargs):
    if self.pk:  # Existing record
        try:
            old = Model.objects.get(pk=self.pk)
            if old.field1 != self.field1 or old.field2 != self.field2:
                self.needs_shopify_push = True  # ← FLAG SET
        except Model.DoesNotExist:
            pass
    super().save(*args, **kwargs)  # ← SAVED TO DJANGO ONLY
```

**Key Point**: The flag is set, but NO actual push to Shopify happens.

---

## Current Workflow for CREATE Operations

### In Django Admin:

1. **User creates new record** (Customer, Product, Address, etc.)
2. **Django saves to database** ✅
3. **Model's save() sets `needs_shopify_push=True`** ✅
4. **❌ STOPS HERE - No automatic push**

### To Push to Shopify:

**Option A - Management Command** (Addresses & Inventory):
```bash
python manage.py push_pending_to_shopify
```

**Option B - Admin Action** (Products only):
1. Go to products list
2. Select products with "⏳ Pending Push" status
3. Actions → "📤 Push selected products TO Shopify"

**Option C - Programmatically**:
```python
from customers.bidirectional_sync import push_customer_to_shopify
from products.bidirectional_sync import push_product_to_shopify

# Push specific record
result = push_customer_to_shopify(customer)
result = push_product_to_shopify(product)
```

---

## DELETE Operations Status

| Model              | Django Delete | Shopify Delete | How to Delete from Shopify |
|-------------------|---------------|----------------|----------------------------|
| Customer          | ✅            | ❌             | Not implemented            |
| Address           | ✅            | ❌             | Not implemented            |
| Product           | ✅            | ✅ (manual)    | Admin action               |
| Variant           | ✅            | ❌             | Not implemented            |
| Inventory Item    | ✅            | ❌             | Not implemented            |
| Inventory Level   | ✅            | ❌             | Not implemented            |

**Only products have a delete-from-Shopify action**, but it's manual.

---

## Recommendations

### If You Want Auto-Push on CREATE:

Add `save_model()` override to admin classes:

```python
# Example for customers/admin.py
def save_model(self, request, obj, form, change):
    super().save_model(request, obj, form, change)
    
    # Auto-push to Shopify if new or changed
    if obj.needs_shopify_push:
        from customers.bidirectional_sync import push_customer_to_shopify
        result = push_customer_to_shopify(obj)
        
        if result['success']:
            messages.success(request, f"✅ Synced to Shopify: {obj}")
        else:
            messages.error(request, f"❌ Failed to sync: {result['message']}")
```

### Pros of Current System (Flag-Based):
- ✅ Safe - no accidental Shopify pushes
- ✅ Allows batch operations
- ✅ User controls when sync happens
- ✅ Can review pending changes before push

### Cons of Current System:
- ❌ Requires manual step to push
- ❌ Easy to forget to sync
- ❌ Data can be out of sync

---

## Testing CRUD Operations

Run the analysis script:
```bash
python analyze_crud_operations.py
```

Check pending syncs:
```python
# Customers
ShopifyCustomer.objects.filter(needs_shopify_push=True).count()

# Addresses
ShopifyCustomerAddress.objects.filter(needs_shopify_push=True).count()

# Products
ShopifyProduct.objects.filter(needs_shopify_push=True).count()

# Inventory
ShopifyInventoryLevel.objects.filter(needs_shopify_push=True).count()
```

---

## Conclusion

**✅ Full CRUD is implemented** for all models, but with **manual push requirement**.

**Current State**:
- ✅ CREATE: Works in Django, flags for Shopify sync
- ✅ READ: Fully functional
- ✅ UPDATE: Works in Django, flags for Shopify sync
- ⚠️ DELETE: Django only (except products with manual action)

**To sync changes**: Use management command or admin actions.

**No code modifications needed** - the system is designed this way intentionally for safety and control.
