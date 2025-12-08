# Understanding Shopify Subscription Pricing & Product Display

## 🎯 **How Shopify Subscriptions Work**

### The Subscription Model:

Shopify subscriptions are **ATTACHED TO PRODUCTS**, not separate products themselves.

```
Product: "Wrath of the Fae Special Edition Omnibus"
  ├── One-time purchase: $110.00
  └── Subscription: "Fantasy Lover's Monthly" - 12% off
```

### What "Box includes" Means:

When you create a subscription selling plan and attach it to a product, the **"Box includes"** list tells customers:

> "When you subscribe to this product monthly, you will receive these items as part of your subscription box"

**It does NOT mean:**
- ❌ These are separate cart line items
- ❌ The price is the sum of all these items
- ❌ This is a different product called "Fantasy Lover's Monthly Box"

**It DOES mean:**
- ✅ This product (Wrath of the Fae) is part of a monthly subscription
- ✅ Every month, subscribers get a box containing these items
- ✅ The subscription is for the RECURRING delivery of this curated collection

---

## 💰 **Pricing Explanation**

### Current Setup:

**Product Price:** $110.00  
**Subscription Discount:** 12% off  
**Subscription Price:** $96.80 (should be calculated)

### Why Cart Shows $110.00:

The cart shows the BASE price. The discount is applied at checkout or shown separately.

Shopify calculates subscription discounts in one of these ways:

1. **Percentage Off** (your current setup):
   - Base price: $110.00
   - Discount: 12%
   - Final price: $96.80

2. **Fixed Amount Off**:
   - Base price: $110.00
   - Discount: -$13.20
   - Final price: $96.80

3. **Fixed Price**:
   - Subscription price: $96.80 (set directly)

---

## 📦 **Understanding "Fantasy Lover's Monthly" Box**

### What Customers Receive:

When a customer subscribes to "Wrath of the Fae Special Edition Omnibus" with the "Fantasy Lover's Monthly" plan:

**Every Month They Get:**
1. Save a Horse, Ride a Dragon Premium Sticker
2. Wrath of the Fae Special Edition Omnibus  
3. Wrath of the Fae Special Edition (US Listing)

**For:** $96.80/month (with 12% discount)

### This is a CURATED BOX SUBSCRIPTION:

- The box is curated by Lavish Library
- Contains multiple items each month
- Subscription price covers the entire box
- Products in the box may vary or be fixed

---

## 🛒 **Cart Display**

### Current Display:

```
Wrath of the Fae Special Edition Omnibus        $110.00
📦 Fantasy Lover's Monthly

Monthly fantasy book and themed accessories 
with 12% discount

Box includes:
  • Save a Horse, Ride a Dragon Premium Sticker
  • Wrath of the Fae Special Edition Omnibus
  • Wrath of the Fae Special Edition (US Listing)
```

### Why This is Correct:

1. **Product Title**: Shows the main product (Wrath of the Fae)
2. **Subscription Badge**: Shows it's part of Fantasy Lover's Monthly
3. **Box Contents**: Lists what comes in the monthly box
4. **Price**: Shows base price (discount applied at checkout)

---

## ✅ **What IS Possible**

### Option 1: Show Discounted Price in Cart ✅

Display both original and discounted price:

```
Wrath of the Fae Special Edition Omnibus
📦 Fantasy Lover's Monthly

Original: $110.00
Subscription Price: $96.80 (save $13.20!)

Box includes: [products list]
```

### Option 2: Custom Product Title for Subscriptions ✅

When subscription is selected, change the display name:

```
Fantasy Lover's Monthly Box                 $96.80
(includes Wrath of the Fae and more)

Box includes: [products list]
```

### Option 3: Line Item Details ✅

Show subscription details as meta info:

```
Wrath of the Fae Special Edition Omnibus
Subscription: Fantasy Lover's Monthly (12% off)
Includes 3 items monthly
Price: $96.80/month
```

---

## ❌ **What is NOT Possible (Shopify Limitations)**

### Cannot Do:

1. **Split box items into separate cart lines**
   - Shopify subscriptions are per-product, not per-box-contents
   - Can't programmatically add multiple items as one subscription

2. **Show aggregate price of all box items**
   - The price is for the SUBSCRIPTION, not the sum of items
   - Items in the box don't have individual prices in this model

3. **Have box as separate product from book**
   - The subscription IS attached to the product
   - Can't make it a standalone "box" product unless you create a new product called "Monthly Box"

---

## 🔧 **Recommended Solution**

### For Your Use Case:

**Option A: Keep Current Model (Recommended)**
- Product: "Wrath of the Fae Special Edition Omnibus"
- Subscription: "Fantasy Lover's Monthly" at $96.80/month
- Description: Lists all items in the box
- ✅ Simple for customers
- ✅ Easy to manage
- ✅ Standard Shopify subscriptions

**Option B: Create Separate Box Product**
- Product: "Fantasy Lover's Monthly Box"
- Price: $96.80/month
- Variants: Each month's box as a variant
- Description: "Includes Wrath of the Fae, stickers, and more"
- ⚠️ More complex to manage
- ⚠️ Need to create new product
- ⚠️ Current product links would break

**Option C: Enhanced Display (What I'm Implementing)**
- Keep current model
- Show discounted price prominently
- Format product list as bullets
- Add subscription badges
- Show savings clearly
- ✅ Best of both worlds

---

## 📝 **Action Items**

### What I've Done:

1. ✅ Format product list as bulleted list
2. ✅ Show description and box contents separately
3. ✅ Add subscription info box in cart

### What I'll Add:

1. 🔄 Display discounted price in cart
2. 🔄 Show savings amount
3. 🔄 Add subscription frequency info
4. 🔄 Enhance checkout display

---

## 💡 **Understanding the Business Model**

### Your Subscription Box:

**"Fantasy Lover's Monthly"** is a curated book box subscription:

- **Monthly delivery** of fantasy romance books + accessories
- **Fixed price** of $96.80/month (12% off retail)
- **Curated selection** by Lavish Library
- **Includes multiple items** each month

This is similar to:
- Book of the Month
- FabFitFun
- Birchbox

The product in your store ("Wrath of the Fae") represents the CURRENT month's box. Next month, you might feature a different book with the same subscription plan.

---

**The pricing IS correct** - $110 is the retail value, $96.80 is the subscription price with 12% off.

Would you like me to enhance the pricing display to show the discount more prominently?




