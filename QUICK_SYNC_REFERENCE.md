# Quick Sync Reference - Lavish Library v2

## 🎯 Which Apps Have Auto-Push to Shopify?

### ✅ **YES - Auto-pushes on every save:**

1. **CUSTOMERS** (`customers/`)
   - Create customer → ✅ Auto-creates in Shopify
   - Update customer → ✅ Auto-updates in Shopify
   - Delete customer → ❌ Django only

2. **CUSTOMER ADDRESSES** (`customers/`)
   - Create address → ✅ Auto-creates in Shopify
   - Update address → ✅ Auto-updates in Shopify
   - Delete address → ❌ Django only

3. **PRODUCTS** (`products/`)
   - Create product → ✅ Auto-creates in Shopify
   - Update product → ✅ Auto-updates in Shopify
   - Delete product → ✅ **Auto-deletes from Shopify**

4. **INVENTORY LEVELS** (`inventory/`)
   - Update quantity → ✅ Auto-updates in Shopify
   - Location change → ✅ Auto-syncs

---

## 🔄 How Auto-Sync Works

### **Step-by-Step Flow:**

```
User Action (Django Admin)
    ↓
Model.save() detects changes
    ↓
Sets needs_shopify_push = True
    ↓
Admin.save_model() or save_formset() triggered
    ↓
Calls push_*_to_shopify() function
    ↓
GraphQL/REST API request to Shopify
    ↓
Success: Clear flag, show ✅ message
Failure: Store error, show ⚠️ message
```

---

## 📋 Admin Code Locations

### **Customers:**
```python
# File: customers/admin.py
# Method: save_model() (line 67)
# Auto-push: YES ✅

def save_model(self, request, obj, form, change):
    super().save_model(request, obj, form, change)
    if obj.needs_shopify_push:
        result = push_customer_to_shopify(obj)
        # Shows success/error message to user
```

### **Addresses:**
```python
# File: customers/admin.py
# Method: save_formset() (line 82)
# Auto-push: YES ✅

def save_formset(self, request, form, formset, change):
    instances = formset.save(commit=True)
    for instance in instances:
        if isinstance(instance, ShopifyCustomerAddress):
            result = push_address_to_shopify(instance)
            # Shows success/error message to user
```

### **Products:**
```python
# File: products/admin.py
# Method: save_model() (line 128)
# Auto-push: YES ✅

def save_model(self, request, obj, form, change):
    super().save_model(request, obj, form, change)
    if obj.needs_shopify_push:
        sync_service = ProductBidirectionalSync()
        result = sync_service.push_product_to_shopify(obj)
        # Shows success/error message to user
```

### **Products Delete:**
```python
# File: products/admin.py
# Method: delete_model() (line 183)
# Auto-delete: YES ✅

def delete_model(self, request, obj):
    sync_service = ProductBidirectionalSync()
    result = sync_service.delete_product_from_shopify(obj)
    super().delete_model(request, obj)
    # Shows success/error message to user
```

### **Inventory:**
```python
# File: inventory/admin.py
# Method: save_formset() (line 101)
# Auto-push: YES ✅

def save_formset(self, request, form, formset, change):
    instances = formset.save(commit=True)
    for instance in instances:
        if hasattr(instance, 'needs_shopify_push'):
            result = push_inventory_to_shopify(instance)
            # Shows success/error message to user
```

---

## 🗂️ Sync Service Files

### **Customer Sync:**
```
File: customers/customer_bidirectional_sync.py
Function: push_customer_to_shopify(customer)
API: GraphQL (customerCreate, customerUpdate)
```

### **Address Sync:**
```
File: customers/address_bidirectional_sync_fixed.py
Function: push_address_to_shopify(address)
API: REST (/admin/api/2024-10/customers/{id}/addresses.json)
```

### **Product Sync:**
```
File: products/bidirectional_sync.py
Class: ProductBidirectionalSync()
Methods: 
  - push_product_to_shopify(product)
  - delete_product_from_shopify(product)
API: GraphQL (productCreate, productUpdate, productDelete)
```

### **Inventory Sync:**
```
File: inventory/bidirectional_sync.py
Class: InventoryBidirectionalSync()
Function: push_inventory_to_shopify(level)
API: GraphQL (inventorySetQuantities)
```

---

## 🎬 User Experience

### **Creating a Customer:**
1. Admin goes to Customers → Add Customer
2. Fills in email, name, phone
3. Clicks "Save"
4. **Immediately sees:** "✅ Customer synced to Shopify: John Doe (ID: gid://shopify/Customer/123)"

### **Updating an Address:**
1. Admin edits customer
2. Changes address inline (city, province, etc.)
3. Clicks "Save"
4. **Immediately sees:** "✅ Address synced to Shopify: New York"

### **Creating a Product:**
1. Admin goes to Products → Add Product
2. Fills in title, description, vendor
3. Clicks "Save"
4. **Immediately sees:** "✅ Product synced to Shopify: Premium Widget (ID: gid://shopify/Product/456)"

### **Updating Inventory:**
1. Admin goes to Inventory Items → Select item
2. Changes "Available" quantity from 10 to 15
3. Clicks "Save"
4. **Immediately sees:** "✅ Inventory synced to Shopify: SKU-123 at 8 Mellifont Street"

---

## 📊 Database Fields

All models track sync status with these fields:

```python
needs_shopify_push = models.BooleanField(default=False)
shopify_push_error = models.TextField(blank=True)
last_pushed_to_shopify = models.DateTimeField(null=True, blank=True)
```

---

## 🔍 Finding Records That Need Sync

### **Check pending syncs:**
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

### **View sync errors:**
```python
# Products with errors
ShopifyProduct.objects.exclude(shopify_push_error='')

# Get error message
product = ShopifyProduct.objects.get(id=1)
print(product.shopify_push_error)
```

---

## 🛠️ Manual Commands

### **Push all pending changes:**
```bash
# All pending addresses and inventory
python manage.py push_pending_to_shopify

# Addresses only
python manage.py push_pending_to_shopify --addresses-only

# Inventory only
python manage.py push_pending_to_shopify --inventory-only
```

### **Admin bulk actions:**
```
Products → Select products → Actions → "📤 Push to Shopify"
Products → Select products → Actions → "🗑️ Delete from Shopify"
```

---

## ⚡ Quick Facts

- **Total apps with auto-push:** 4 (customers, addresses, products, inventory)
- **Auto-push trigger:** Django admin `save_model()` or `save_formset()`
- **User feedback:** Immediate success/error messages
- **Sync speed:** ~1-2 seconds per record
- **Error handling:** Errors stored in database, user notified
- **Test protection:** Records with `test_` or `temp_` IDs never pushed

---

## ✅ Summary

**Your system auto-pushes to Shopify for:**
- ✅ Customer CREATE
- ✅ Customer UPDATE
- ✅ Address CREATE
- ✅ Address UPDATE
- ✅ Product CREATE
- ✅ Product UPDATE
- ✅ Product DELETE
- ✅ Inventory UPDATE

**All sync happens automatically on admin submit. No manual steps required!**

---

**Last Updated:** December 6, 2025

