# Quick Reference: Checkout System Issues

## 🔴 THREE CRITICAL BUGS BLOCKING CHECKOUT

---

## Bug #1: Wrong Database Field Name ⚠️ CRITICAL

**File:** `app/lavish_backend/customer_subscriptions/api_views.py`  
**Line:** 55

```python
# ❌ WRONG (Current):
product = ShopifyProduct.objects.get(shopify_product_id=product_id)

# ✅ CORRECT (Should be):
product = ShopifyProduct.objects.get(shopify_id=product_id)
```

**Why it fails:** Field `shopify_product_id` doesn't exist in database.  
**Impact:** Subscription options never load on product pages.

---

## Bug #2: Checkout Not Implemented ⚠️ CRITICAL

**File:** `app/lavish_backend/customer_subscriptions/api_views.py`  
**Lines:** 138-154

```python
# TODO: Implement Shopify checkout creation
# This would create a subscription contract draft in Shopify
# and return a checkout URL for the customer

return Response({
    'message': 'Subscription checkout creation is not yet implemented',
}, status=status.HTTP_501_NOT_IMPLEMENTED)  # ❌ STUB CODE
```

**Why it fails:** Endpoint exists but does nothing.  
**Impact:** Even if Bug #1 fixed, checkout still fails.

---

## Bug #3: Missing Request Data ⚠️ HIGH

**File:** `app/crave_theme/snippets/product-subscription-options.liquid`  
**Lines:** 477-481

```javascript
// ❌ Frontend sends:
{
  "selling_plan_id": 1,
  "product_id": "123",
  "quantity": 1
  // Missing: customer_id ❌
  // Missing: variant_id ❌
}

// ✅ Backend expects:
{
  "customer_id": "...",      // ❌ Not sent
  "selling_plan_id": "...",  // ✅ Sent
  "variant_id": "...",       // ❌ Not sent
  "quantity": 1              // ✅ Sent
}
```

**Why it fails:** Backend validation requires all fields.  
**Impact:** Even if Bug #1 & #2 fixed, validation fails.

---

## Quick Test to Confirm

```bash
# Run this command to see Bug #1 in action:
curl http://127.0.0.1:8003/api/subscriptions/selling-plans/?product_id=123

# Expected error:
# "Cannot resolve keyword 'shopify_product_id' into field"
```

---

## Recommended Solution

### Option A: Shopify Native (EASY - 2 hours) ⭐

Use Shopify's built-in subscription checkout:

```javascript
// Add to cart with subscription
fetch('/cart/add.js', {
  body: JSON.stringify({
    id: variantId,
    quantity: 1,
    selling_plan: sellingPlanId
  })
});

// Redirect to Shopify checkout
window.location.href = '/checkout';
```

**Pros:**
- ✅ Only need to fix Bug #1
- ✅ No backend implementation needed
- ✅ Shopify handles payments
- ✅ Works immediately

---

## File Locations

| Issue | File Path | Line |
|-------|-----------|------|
| Bug #1 | `app/lavish_backend/customer_subscriptions/api_views.py` | 55 |
| Bug #2 | `app/lavish_backend/customer_subscriptions/api_views.py` | 138 |
| Bug #3 | `app/crave_theme/snippets/product-subscription-options.liquid` | 477 |

---

## Current vs Expected Behavior

| Step | Current (BROKEN) | Expected (WORKING) |
|------|-----------------|-------------------|
| Load page | ✅ Works | ✅ Works |
| Load options | ❌ Error 500 | ✅ Shows plans |
| Click subscribe | ❌ Error 501 | ✅ Goes to checkout |
| Complete purchase | ❌ Never reached | ✅ Subscription created |

---

**See `CHECKOUT_FAILURE_DIAGNOSIS.md` for complete analysis**

