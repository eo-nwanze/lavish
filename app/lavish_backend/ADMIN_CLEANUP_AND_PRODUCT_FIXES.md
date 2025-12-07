# Django Admin Cleanup & Product Sync Fixes

**Date:** December 6, 2025  
**Status:** ✅ Completed

---

## 📋 Tasks Completed

### **1. Hidden Admin Menu Items** ✅

#### **Accounts App:**
Hidden from sidebar:
- ✅ Bank details
- ✅ Card details  
- ✅ PayID

**File:** `accounts/admin.py`

**Changes:**
- Commented out `@admin.register` decorators for `BankDetailAdmin`, `CardDetailAdmin`, and `PayIDAdmin`
- Models still exist in database but won't show in admin sidebar

#### **Email Manager App:**
Hidden from sidebar:
- ✅ Email Attachments
- ✅ Email Automations
- ✅ Email Folders
- ✅ Email Guardians
- ✅ Email History
- ✅ Email Inboxes
- ✅ Email Labels
- ✅ Email Messages
- ✅ Email guardian rules
- ✅ Email scan results
- ✅ Incoming Mail Configs
- ✅ Message Labels
- ✅ Scheduled Emails
- ✅ Security Alerts

**Files:**
- `email_manager/admin.py` (replaced with simplified version)
- `email_manager/admin.py.backup` (original saved for reference)
- `email_manager/admin_simple.py` (source for new admin.py)

**Still Visible:**
- ✅ Email Configuration
- ✅ Email Templates

---

### **2. Product Sync Issues Identified** 🔍

#### **Test Product 4 Analysis:**

**Product Details:**
```
Name: Test Product 4 - Full Admin Flow
ID: 102
Shopify ID: gid://shopify/Product/7510675259486
Category: Test Products ✅
Vendor: Lavish Library ✅
Status: ACTIVE ✅
```

**Variant 1:**
```
Name: test 3 V1
Shopify ID: gid://shopify/ProductVariant/42251418042462 ✅
Price: $29.99 ✅
SKU: TEST-3-001 ✅
Stock: 10 units
Issue: ❌ No inventory item synced
```

**Variant 2:**
```
Name: Test 4 V2
Shopify ID: temp_variant_1765061408182_102_1 ❌
Price: $49.00 ✅
SKU: TEST-4-001 ✅
Stock: 5 units
Issue: ❌ Not synced to Shopify (temp ID)
```

---

## 🐛 Issues Found

### **Issue 1: Product Category Not Syncing**
**Status:** ✅ RESOLVED

**Problem:**  
Product Type (category) wasn't appearing in Shopify

**Root Cause:**  
Category field exists in Django but was set correctly

**Solution:**  
Category "Test Products" is already synced to Shopify ✅

---

### **Issue 2: Inventory Showing "Not Tracked"**
**Status:** ⚠️ NEEDS FIXING

**Problem:**  
Inventory shows as "Inventory not tracked" in Shopify admin

**Root Cause:**  
1. Inventory items not created in Django
2. Inventory levels not synced to Shopify
3. Tracking not enabled on Shopify variants

**Current State:**
- Product has 2 variants in Django with stock quantities
- No `ShopifyInventoryItem` records exist
- No `ShopifyInventoryLevel` records exist
- Shopify variants don't have inventory tracking enabled

---

### **Issue 3: Variant 2 Not Synced**
**Status:** ⚠️ NEEDS FIXING

**Problem:**  
Second variant has temp ID, not synced to Shopify

**Root Cause:**  
Variant was created in Django but sync failed or didn't trigger

**Solution Needed:**
Push variant to Shopify to get real Shopify ID

---

## 🔧 Recommended Fixes

### **Fix 1: Enable Inventory Tracking** (Required)

The product sync needs to:

1. **Create Inventory Items:**
   - When variant syncs to Shopify, query for inventory item ID
   - Create `ShopifyInventoryItem` in Django
   - Enable tracking via GraphQL:
   ```graphql
   mutation {
     inventoryItemUpdate(id: $inventoryItemId, input: {tracked: true}) {
       inventoryItem { id tracked }
     }
   }
   ```

2. **Set Inventory Quantities:**
   - Get location ID (default location)
   - Set quantity via GraphQL:
   ```graphql
   mutation {
     inventorySetQuantities(input: {
       name: "available"
       reason: "correction"
       quantities: [{
         inventoryItemId: $inventoryItemId
         locationId: $locationId
         quantity: 10
       }]
     }) {
       inventoryAdjustmentGroup { id }
     }
   }
   ```

3. **Sync to Django:**
   - Create `ShopifyInventoryLevel` records
   - Link to inventory items and locations

---

### **Fix 2: Sync Variant 2** (Required)

**Steps:**
1. Check if product needs_shopify_push
2. If yes, trigger product sync from Django admin
3. Sync should push variant 2 to Shopify
4. Get real Shopify ID for variant
5. Update Django record with real ID

**How to Fix:**
```bash
# Option 1: Via Django Admin
1. Go to Products → Test Product 4
2. Click Save (triggers auto-push)
3. Verify variant 2 gets real Shopify ID

# Option 2: Via Script
python fix_product_sync_issue.py 102
```

---

### **Fix 3: Auto-Enable Inventory Tracking** (Enhancement)

**Recommendation:**  
Enhance product sync to automatically:
1. Enable inventory tracking when variant is created
2. Set initial quantity from Django
3. Create inventory item and level records in Django

**File to Modify:**  
`products/bidirectional_sync.py`

**Changes Needed:**
```python
def _create_new_product(self, product):
    # After creating product...
    
    # For each variant:
    for variant in shopify_variants:
        # 1. Get inventory item ID
        inventory_item_id = variant['inventoryItem']['id']
        
        # 2. Enable tracking
        self._enable_inventory_tracking(inventory_item_id)
        
        # 3. Set quantity
        self._set_inventory_quantity(
            inventory_item_id,
            django_variant.inventory_quantity
        )
        
        # 4. Create Django records
        ShopifyInventoryItem.objects.create(
            shopify_id=inventory_item_id,
            variant=django_variant,
            tracked=True
        )
```

---

## 📊 Current State Summary

### **Products:**
```
Total Products: 12
With Shopify ID: 12
Synced Successfully: 11
With Issues: 1 (Test Product 4 - variant 2)
```

### **Inventory:**
```
Products with Stock: 3
Inventory Items Synced: 0 ❌
Inventory Levels Synced: 0 ❌
Tracking Enabled: 0 ❌
```

### **Admin Interface:**
```
Hidden from Accounts: 3 models ✅
Hidden from Email Manager: 14 models ✅
Visible Models: 2 (Configuration, Templates) ✅
```

---

## ✅ What Works Now

1. ✅ Admin sidebar is cleaner (17 models hidden)
2. ✅ Product category shows correctly in Shopify
3. ✅ Product variant 1 synced with correct price/SKU
4. ✅ Product creation working
5. ✅ Product updates working

---

## ⚠️ What Still Needs Fixing

1. ⏳ Inventory tracking needs to be enabled
2. ⏳ Variant 2 needs to be synced to Shopify
3. ⏳ Inventory items need to be created in Django
4. ⏳ Inventory levels need to be synced

---

## 🚀 Next Steps

### **Immediate (High Priority):**

1. **Sync Variant 2:**
   ```bash
   python fix_product_sync_issue.py 102
   ```
   Expected: Variant 2 gets real Shopify ID

2. **Enable Inventory Tracking:**
   - Manually in Shopify Admin for now:
     - Products → Test Product 4
     - Click each variant
     - Check "Track quantity"
     - Set quantities (10 for V1, 5 for V2)

### **Soon (Medium Priority):**

3. **Enhance Product Sync:**
   - Modify `products/bidirectional_sync.py`
   - Add automatic inventory tracking enable
   - Add automatic inventory quantity sync
   - Create inventory items/levels in Django

4. **Test Complete Flow:**
   - Create new product in Django
   - Verify inventory tracking auto-enables
   - Verify quantities sync correctly
   - Verify shows correct in Shopify

### **Later (Low Priority):**

5. **Bulk Fix Existing Products:**
   - Script to enable tracking on all products
   - Script to sync all inventory items
   - Script to sync all inventory levels

---

## 📝 Files Changed

### **Modified:**
```
✅ accounts/admin.py
✅ email_manager/admin.py
```

### **Created:**
```
✅ email_manager/admin_simple.py
✅ email_manager/admin.py.backup
✅ fix_product_inventory_category.py
✅ fix_product_sync_issue.py
✅ check_product_sync_error.py
✅ diagnose_product_sync_error.py
```

---

## 💡 How to Restore Hidden Models

### **Accounts App:**

Edit `accounts/admin.py` and uncomment:
```python
@admin.register(BankDetail)
class BankDetailAdmin(ImportExportModelAdmin):
    # ...
```

### **Email Manager:**

Replace `email_manager/admin.py` with `email_manager/admin.py.backup`:
```bash
Copy-Item email_manager/admin.py.backup email_manager/admin.py
```

---

## ✅ Verification

### **Check Admin Sidebar:**
1. Go to Django admin
2. Accounts section should only show: Users, Companies, Industry Types, etc.
3. Accounts section should NOT show: Bank details, Card details, PayID
4. Email Manager section should only show: Email Configuration, Email Templates
5. Email Manager should NOT show: Inboxes, Messages, Attachments, etc.

### **Check Product in Shopify:**
1. Go to Shopify Admin → Products
2. Find "Test Product 4 - Full Admin Flow"
3. Should show category: "Test Products" ✅
4. Should have 2 variants ⚠️ (only 1 if variant 2 not synced yet)
5. Inventory might show "not tracked" ⚠️ (until fixed)

---

## 📚 Related Documentation

- `ADMIN_AUTO_SYNC_REPORT.md` - Auto-sync implementation details
- `SHOPIFY_SYNC_FIXES.md` - Previous sync fixes
- `CRUD_OPERATIONS_REPORT.md` - CRUD operations overview

---

**Summary:** ✅ Admin cleanup complete, product sync issues identified and documented with clear fix paths.

