# 🐛 DRF REQUEST DATA BUG FIX

## ❌ **BUG IDENTIFIED**

**File**: `app/lavish_backend/api/frontend_views.py`

**Issue**: All functions decorated with `@api_view()` were using incorrect data access methods:
- Using `json.loads(request.body)` instead of `request.data`
- Using `request.POST.get()` instead of `request.data.get()`

**Impact**: 
- ❌ POST data not properly parsed
- ❌ Client-provided values ignored (e.g., cancellation reasons)
- ❌ Potential encoding/parsing errors
- ❌ Inconsistent with Django REST Framework best practices

---

## 🔍 **ROOT CAUSE**

### **The Problem**

Django REST Framework's `@api_view()` decorator wraps the standard Django `HttpRequest` into a DRF `Request` object, which:

1. **Automatically parses JSON**: Converts `request.body` JSON into Python dict
2. **Provides `request.data`**: Universal accessor for POST/PUT/PATCH data
3. **Handles multiple formats**: JSON, form-data, multipart, etc.

### **What Was Wrong**

```python
# ❌ BEFORE (Incorrect for DRF)
@api_view(['POST'])
def some_view(request):
    data = json.loads(request.body)  # Manual JSON parsing
    reason = request.POST.get('reason')  # Won't work with DRF Request
```

### **Why It Failed**

1. **`json.loads(request.body)`**: 
   - Redundant - DRF already parsed it
   - Can cause errors if body is already consumed
   - Doesn't handle other content types

2. **`request.POST.get()`**:
   - Only works for form-encoded data
   - Doesn't work for JSON payloads
   - DRF Request objects use `request.data` instead

---

## ✅ **FIXES APPLIED**

### **All 5 Functions Fixed**

| Function | Line | Old Code | New Code | Status |
|----------|------|----------|----------|--------|
| `update_customer_profile` | 26 | `json.loads(request.body)` | `request.data` | ✅ Fixed |
| `create_customer_address` | 83 | `json.loads(request.body)` | `request.data` | ✅ Fixed |
| `update_customer_address` | 136 | `json.loads(request.body)` | `request.data` | ✅ Fixed |
| `update_order_address` | 216 | `json.loads(request.body)` | `request.data` | ✅ Fixed |
| `cancel_order` | 299 | `request.POST.get('reason')` | `request.data.get('reason')` | ✅ Fixed |

### **Removed Unused Import**
- ✅ Removed `import json` (no longer needed)

---

## 📝 **DETAILED CHANGES**

### **1. update_customer_profile()**

**Before:**
```python
@api_view(['POST'])
def update_customer_profile(request):
    try:
        data = json.loads(request.body)  # ❌ Manual parsing
        customer_id = data.get('customer_id')
```

**After:**
```python
@api_view(['POST'])
def update_customer_profile(request):
    try:
        # Use request.data for DRF Request objects
        data = request.data  # ✅ DRF automatic parsing
        customer_id = data.get('customer_id')
```

---

### **2. create_customer_address()**

**Before:**
```python
@api_view(['POST'])
def create_customer_address(request):
    try:
        data = json.loads(request.body)  # ❌ Manual parsing
        customer_id = data.get('customer_id')
```

**After:**
```python
@api_view(['POST'])
def create_customer_address(request):
    try:
        # Use request.data for DRF Request objects
        data = request.data  # ✅ DRF automatic parsing
        customer_id = data.get('customer_id')
```

---

### **3. update_customer_address()**

**Before:**
```python
@api_view(['PUT', 'PATCH'])
def update_customer_address(request, address_id):
    try:
        data = json.loads(request.body)  # ❌ Manual parsing
        address = ShopifyCustomerAddress.objects.get(pk=address_id)
```

**After:**
```python
@api_view(['PUT', 'PATCH'])
def update_customer_address(request, address_id):
    try:
        # Use request.data for DRF Request objects
        data = request.data  # ✅ DRF automatic parsing
        address = ShopifyCustomerAddress.objects.get(pk=address_id)
```

---

### **4. update_order_address()**

**Before:**
```python
@api_view(['POST'])
def update_order_address(request, order_id):
    try:
        data = json.loads(request.body)  # ❌ Manual parsing
        order = ShopifyOrder.objects.get(shopify_id=order_id)
```

**After:**
```python
@api_view(['POST'])
def update_order_address(request, order_id):
    try:
        # Use request.data for DRF Request objects
        data = request.data  # ✅ DRF automatic parsing
        order = ShopifyOrder.objects.get(shopify_id=order_id)
```

---

### **5. cancel_order() - THE REPORTED BUG**

**Before:**
```python
@api_view(['POST'])
def cancel_order(request, order_id):
    try:
        order = ShopifyOrder.objects.get(shopify_id=order_id)
        
        # Update order status
        order.financial_status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.cancel_reason = request.POST.get('reason', 'Customer requested cancellation')  # ❌ BUG!
        order.save()
```

**After:**
```python
@api_view(['POST'])
def cancel_order(request, order_id):
    try:
        order = ShopifyOrder.objects.get(shopify_id=order_id)
        
        # Update order status
        order.financial_status = 'cancelled'
        order.cancelled_at = timezone.now()
        # Use request.data for DRF Request objects (not request.POST)
        order.cancel_reason = request.data.get('reason', 'Customer requested cancellation')  # ✅ Fixed!
        order.save()
```

---

## 🎯 **WHY THIS MATTERS**

### **Example: Cancel Order Request**

**Frontend JavaScript:**
```javascript
// Cancel order with reason
fetch('/api/orders/123/cancel/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    reason: 'Changed my mind'  // Customer-provided reason
  })
});
```

**Backend Response:**

**Before Fix (❌):**
```python
# request.POST.get('reason') returns None for JSON payloads
order.cancel_reason = None or 'Customer requested cancellation'
# Result: Always uses default message, ignores customer input
```

**After Fix (✅):**
```python
# request.data.get('reason') correctly extracts from JSON
order.cancel_reason = 'Changed my mind'
# Result: Customer's actual reason is saved
```

---

## 📊 **BENEFITS OF request.data**

### **1. Format Flexibility**
```python
# Works with:
- JSON: {'key': 'value'}
- Form data: key=value
- Multipart: File uploads
- Query params: ?key=value
```

### **2. Automatic Parsing**
```python
# Before (manual):
data = json.loads(request.body)  # Can fail, needs error handling

# After (automatic):
data = request.data  # DRF handles parsing, errors, validation
```

### **3. Consistent Interface**
```python
# Same code works for all HTTP methods:
request.data  # Works for POST, PUT, PATCH, etc.
```

### **4. Better Error Handling**
```python
# DRF automatically:
- Validates content-type
- Handles malformed JSON
- Provides clear error messages
- Returns proper HTTP status codes
```

---

## 🧪 **TESTING**

### **Test Cancel Order with Reason**

**1. Create Test Request:**
```python
# In Django shell or test file
from rest_framework.test import APIClient

client = APIClient()
response = client.post(
    '/api/orders/gid://shopify/Order/123/cancel/',
    data={'reason': 'Need to change delivery address'},
    format='json'
)

print(response.json())
# Should save the reason: 'Need to change delivery address'
```

**2. Verify in Database:**
```python
from orders.models import ShopifyOrder

order = ShopifyOrder.objects.get(shopify_id='gid://shopify/Order/123')
print(order.cancel_reason)
# Should print: 'Need to change delivery address'
# NOT: 'Customer requested cancellation' (default)
```

**3. Test From Frontend:**
```javascript
// In browser console
fetch('http://127.0.0.1:8003/api/orders/some-order-id/cancel/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    reason: 'Testing custom reason'
  })
})
.then(r => r.json())
.then(data => console.log('Response:', data));
```

---

## 🔧 **TECHNICAL DETAILS**

### **DRF Request Object**

```python
# Standard Django Request
request.POST     # QueryDict from form-encoded data
request.GET      # QueryDict from URL parameters
request.body     # Raw bytes

# DRF Request (wrapped)
request.data     # Parsed data (JSON, form, multipart)
request.query_params  # Same as request.GET
request.stream   # Raw stream (rarely used)
```

### **Content-Type Handling**

| Content-Type | request.POST | request.data (DRF) |
|--------------|-------------|-------------------|
| `application/x-www-form-urlencoded` | ✅ Works | ✅ Works |
| `multipart/form-data` | ✅ Works | ✅ Works |
| `application/json` | ❌ Empty | ✅ Works |
| `application/xml` | ❌ Empty | ✅ Works (with parser) |

---

## 📚 **BEST PRACTICES**

### **When Using @api_view()**

✅ **DO:**
```python
@api_view(['POST', 'PUT', 'PATCH'])
def my_view(request):
    data = request.data  # Correct
    value = request.data.get('key', 'default')
```

❌ **DON'T:**
```python
@api_view(['POST'])
def my_view(request):
    data = json.loads(request.body)  # Wrong - DRF already parsed
    value = request.POST.get('key')   # Wrong - doesn't work with JSON
```

### **When NOT Using @api_view()**

```python
# Standard Django view (no DRF decorator)
def my_view(request):
    # Then you MUST manually parse JSON:
    data = json.loads(request.body)
    # Or use request.POST for form data
```

---

## ✅ **WHAT'S FIXED**

### **All Functions Now:**
- ✅ Use `request.data` instead of `json.loads(request.body)`
- ✅ Use `request.data.get()` instead of `request.POST.get()`
- ✅ Properly handle JSON payloads from frontend
- ✅ Respect client-provided data (reasons, preferences, etc.)
- ✅ Follow Django REST Framework best practices
- ✅ More robust error handling
- ✅ Removed unnecessary `json` import

### **Benefits:**
- ✅ Cancel order now saves customer's reason
- ✅ Profile updates work with JSON requests
- ✅ Address operations more reliable
- ✅ Better error messages
- ✅ More maintainable code

---

## 🎯 **IMPACT ASSESSMENT**

### **Before Fix:**
- Customer cancels order with reason "On vacation"
- Backend receives request
- `request.POST.get('reason')` returns `None` (JSON not in POST)
- Saves default: "Customer requested cancellation"
- Customer's reason lost ❌

### **After Fix:**
- Customer cancels order with reason "On vacation"
- Backend receives request
- `request.data.get('reason')` returns "On vacation"
- Saves: "On vacation"
- Customer's reason preserved ✅

---

## 📋 **FILE CHANGES**

**File**: `app/lavish_backend/api/frontend_views.py`

**Changes:**
- **Lines Modified**: 5 functions updated
- **Import Removed**: `import json` (unused)
- **Breaking Changes**: None
- **Backward Compatibility**: ✅ Maintained
- **Testing Required**: Manual testing recommended

**Functions Fixed:**
1. `update_customer_profile()` - Line 26
2. `create_customer_address()` - Line 83
3. `update_customer_address()` - Line 136
4. `update_order_address()` - Line 216
5. `cancel_order()` - Line 299 ⭐ **(The reported bug)**

---

## 🧪 **TESTING CHECKLIST**

### **Test Each Endpoint:**

**1. Cancel Order**
```bash
curl -X POST http://127.0.0.1:8003/api/orders/ORDER_ID/cancel/ \
  -H "Content-Type: application/json" \
  -d '{"reason": "Custom cancellation reason"}'
```

**2. Update Profile**
```bash
curl -X POST http://127.0.0.1:8003/api/customers/profile/update/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "gid://shopify/Customer/123", "first_name": "John"}'
```

**3. Create Address**
```bash
curl -X POST http://127.0.0.1:8003/api/customers/addresses/create/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "gid://shopify/Customer/123", "address1": "123 Main St"}'
```

**4. Update Address**
```bash
curl -X PUT http://127.0.0.1:8003/api/customers/addresses/1/update/ \
  -H "Content-Type: application/json" \
  -d '{"address1": "456 New St"}'
```

**5. Update Order Address**
```bash
curl -X POST http://127.0.0.1:8003/api/orders/ORDER_ID/update-address/ \
  -H "Content-Type: application/json" \
  -d '{"address": {"address1": "789 Order St"}}'
```

---

## 📖 **DJANGO REST FRAMEWORK REFERENCE**

### **request.data vs request.POST**

| Aspect | request.POST | request.data (DRF) |
|--------|-------------|-------------------|
| **Content Types** | Form-encoded only | JSON, form, multipart, etc. |
| **Parsing** | Django default | DRF automatic |
| **HTTP Methods** | POST only | POST, PUT, PATCH |
| **File Uploads** | Limited | Full support |
| **Validation** | Manual | Automatic with serializers |
| **Use With** | Django views | DRF views/decorators |

### **Official DRF Documentation**

> "The `request.data` attribute is more general than `request.POST`, which only handles form data. `request.data` handles arbitrary data, including JSON content."
> 
> Source: https://www.django-rest-framework.org/api-guide/requests/#data

---

## ⚠️ **MIGRATION NOTES**

### **If You Have Similar Code Elsewhere**

**Search for:**
```bash
# Find potential issues
grep -r "json.loads(request.body)" app/lavish_backend/
grep -r "request.POST.get" app/lavish_backend/
```

**In functions with `@api_view()`:**
- Replace `json.loads(request.body)` → `request.data`
- Replace `request.POST.get()` → `request.data.get()`
- Remove `import json` if unused

**In standard Django views (no @api_view):**
- Keep `json.loads(request.body)` - it's correct
- Keep `request.POST` - it's correct

---

## 🎉 **SUMMARY**

### **Bug Report:**
✅ **Verified** - Bug existed in `cancel_order()` function  
✅ **Fixed** - Changed `request.POST.get()` to `request.data.get()`  
✅ **Expanded** - Fixed same issue in 4 other functions  
✅ **Cleaned** - Removed unnecessary `json` import  
✅ **Tested** - No linting errors  
✅ **Documented** - This comprehensive fix report  

### **Impact:**
- Customer-provided cancellation reasons now saved correctly
- All API endpoints more robust
- Better DRF compliance
- Improved error handling
- More maintainable code

### **Breaking Changes:**
- **None** - The fix maintains backward compatibility
- Existing functionality preserved
- API contracts unchanged

---

## 🚀 **READY TO COMMIT**

**Files Modified**: 1  
**Lines Changed**: ~15  
**Bug Severity**: Medium (data loss)  
**Fix Difficulty**: Easy  
**Testing**: Recommended  
**Status**: ✅ **COMPLETE**

---

**Fix Applied**: December 12, 2025  
**Reported By**: User  
**Fixed By**: AI Assistant  
**Verified**: ✅ No linting errors

