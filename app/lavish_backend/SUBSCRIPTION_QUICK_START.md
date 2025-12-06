# Subscription Quick Start Guide

## 🚀 Creating Your First Subscription in Django

### **Step 1: Create a Selling Plan** ⭐

1. Go to Django Admin → **Customer Subscriptions** → **Selling Plans** → **Add Selling Plan**

2. Fill in the details:
   ```
   Name: Monthly Box
   Description: Get our monthly box delivered
   
   Billing Policy: RECURRING
   Billing Interval: MONTH
   Billing Interval Count: 1
   
   Price Adjustment Type: PERCENTAGE
   Price Adjustment Value: 10 (for 10% off)
   
   Delivery Policy: RECURRING
   Delivery Interval: MONTH
   Delivery Interval Count: 1
   
   Is Active: ✅ Checked
   ```

3. **Optional:** Associate with products in the "Products" field

4. Click **"Save"**

5. **Result:** ✅ "Selling Plan synced to Shopify: Monthly Box (ID: gid://shopify/SellingPlan/...)"

---

### **Step 2: Create a Customer Subscription** ⭐

1. **Prerequisites:**
   - Customer must have a Shopify ID (sync customer first if needed)
   - Product variant must exist in Shopify

2. Go to Django Admin → **Customer Subscriptions** → **Customer Subscriptions** → **Add**

3. Fill in basic info:
   ```
   Customer: John Doe (select from dropdown)
   Selling Plan: Monthly Box (select the plan you created)
   Status: ACTIVE
   Currency: USD
   ```

4. Fill in billing schedule:
   ```
   Next Billing Date: 2025-12-15
   Billing Policy Interval: MONTH
   Billing Policy Interval Count: 1
   ```

5. Fill in delivery schedule:
   ```
   Next Delivery Date: 2025-12-15
   Delivery Policy Interval: MONTH
   Delivery Policy Interval Count: 1
   ```

6. Add line items (products to subscribe to):
   ```json
   [
     {
       "variant_id": "gid://shopify/ProductVariant/123456789",
       "quantity": 1,
       "current_price": "29.99",
       "selling_plan_id": "gid://shopify/SellingPlan/987654321"
     }
   ]
   ```

7. Add delivery address:
   ```json
   {
     "first_name": "John",
     "last_name": "Doe",
     "address1": "123 Main St",
     "address2": "Apt 4B",
     "city": "New York",
     "province": "NY",
     "country": "United States",
     "zip": "10001",
     "phone": "+1234567890"
   }
   ```

8. **Optional:** Add payment method ID if available

9. Click **"Save"**

10. **Result:** ✅ "Subscription created in Shopify for John Doe (ID: gid://shopify/SubscriptionContract/...)"

---

### **Step 3: Bill the Subscription (Create an Order)** 💳

1. Go to Django Admin → **Customer Subscriptions** → **Customer Subscriptions**

2. Find your subscription in the list

3. Check the box next to it

4. In the "Actions" dropdown, select **"💳 Create Billing Attempts (Bill & Create Orders)"**

5. Click **"Go"**

6. **Result:** ✅ "Billing attempt created for subscription 1. Order: #1001"

7. An order is created in Shopify and the customer is charged!

---

## 📋 Common Line Item Formats

### **Simple Line Item (No Selling Plan):**
```json
[
  {
    "variant_id": "gid://shopify/ProductVariant/123456789",
    "quantity": 1,
    "current_price": "29.99"
  }
]
```

### **Line Item with Selling Plan:**
```json
[
  {
    "variant_id": "gid://shopify/ProductVariant/123456789",
    "quantity": 1,
    "current_price": "29.99",
    "selling_plan_id": "gid://shopify/SellingPlan/987654321"
  }
]
```

### **Multiple Line Items:**
```json
[
  {
    "variant_id": "gid://shopify/ProductVariant/123456789",
    "quantity": 2,
    "current_price": "29.99"
  },
  {
    "variant_id": "gid://shopify/ProductVariant/987654321",
    "quantity": 1,
    "current_price": "49.99"
  }
]
```

---

## 🔍 How to Find IDs

### **Finding Customer Shopify ID:**
1. Go to **Customers** → Select customer
2. Look for "Shopify id" field
3. Should look like: `gid://shopify/Customer/123456789`

### **Finding Product Variant ID:**
1. Go to **Products** → Select product
2. Click on **Variants** tab or scroll down to variants
3. Look for "Shopify id" field in variant
4. Should look like: `gid://shopify/ProductVariant/123456789`

### **Finding Selling Plan ID:**
1. Go to **Customer Subscriptions** → **Selling Plans**
2. Click on your selling plan
3. Look for "Shopify id" field
4. Should look like: `gid://shopify/SellingPlan/123456789`

---

## ⚡ Quick Actions

### **Update Subscription:**
1. Edit subscription in admin
2. Change fields (next billing date, line items, etc.)
3. Click "Save"
4. ✅ Auto-updates in Shopify

### **Cancel Subscription:**
1. Select subscription(s)
2. Actions → "🗑️ Cancel subscriptions IN Shopify"
3. Click "Go"
4. ✅ Cancelled in Shopify, status updated to CANCELLED

### **Push Multiple Plans:**
1. Go to **Selling Plans**
2. Select multiple plans
3. Actions → "📤 Push selling plans TO Shopify"
4. Click "Go"
5. ✅ All selected plans pushed to Shopify

---

## 💡 Tips & Best Practices

### **1. Always Sync Customers First**
Before creating subscriptions, make sure the customer exists in Shopify:
- Create customer in Django Admin
- Wait for "✅ Customer synced to Shopify" message
- Then create subscription

### **2. Use Subscription Addresses**
Create a `SubscriptionAddress` for your customer:
- Go to **Subscription Addresses** → Add
- Select customer
- Fill in address
- This becomes the default delivery address

### **3. Test with Small Amounts First**
When testing billing:
- Use small prices (e.g., $0.01)
- Test in Shopify's test mode
- Verify orders are created correctly

### **4. Monitor Billing Attempts**
Check **Subscription Billing Attempts** to see:
- Which subscriptions were billed
- Which orders were created
- Any errors that occurred

### **5. Handle Payment Methods**
- Subscriptions can be created without payment methods
- Customer can add payment method in Shopify customer accounts
- Use webhook `customer_payment_methods/create` to track new payment methods

---

## ❌ Common Errors & Solutions

### **Error: "Customer has no Shopify ID"**
**Solution:** Sync the customer to Shopify first
```
1. Go to Customers
2. Find customer
3. Click Save (auto-syncs)
4. Verify "Shopify id" field is populated
5. Try creating subscription again
```

### **Error: "Subscription must have a delivery address"**
**Solution:** Add delivery address JSON or create SubscriptionAddress
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "address1": "123 Main St",
  "city": "New York",
  "province": "NY",
  "country": "United States",
  "zip": "10001"
}
```

### **Error: "Failed to add line item"**
**Solution:** Verify product variant ID is correct
```
1. Go to Products
2. Find product
3. Check variant Shopify ID
4. Copy exact GID format: gid://shopify/ProductVariant/123456789
```

### **Error: "Payment method required"**
**Note:** Payment method is optional for creating subscription
- Subscription will be created successfully
- Customer can add payment method later
- Billing attempt will fail without payment method
- Customer should add payment in customer accounts

---

## 📊 Monitoring & Tracking

### **Check Sync Status:**
```
1. Go to Selling Plans or Subscriptions list
2. Look for "Needs shopify push" column
3. True = Pending sync
4. False = Synced
```

### **View Sync Errors:**
```
1. Edit a record
2. Scroll to "Sync Status" section
3. Check "Shopify push error" field
4. Shows last error message
```

### **View Billing Attempts:**
```
1. Go to Subscription Billing Attempts
2. Filter by status (SUCCESS, FAILED, PENDING)
3. View order IDs created
4. Check error messages for failed attempts
```

---

## 🎯 Complete Example

### **Create Monthly Coffee Subscription:**

**1. Create Selling Plan:**
```
Name: Monthly Coffee Subscription
Billing Interval: MONTH (1)
Delivery Interval: MONTH (1)
Price Adjustment: 15% off
```

**2. Create Subscription for Customer:**
```
Customer: Jane Smith
Plan: Monthly Coffee Subscription
Next Billing: 2025-12-15
Line Items: [
  {
    "variant_id": "gid://shopify/ProductVariant/44207103082566",
    "quantity": 1,
    "current_price": "24.99",
    "selling_plan_id": "gid://shopify/SellingPlan/3801940038"
  }
]
Delivery Address: Jane's home address
```

**3. Bill Subscription:**
```
Actions → Create Billing Attempts
Result: Order #1001 created for $21.24 ($24.99 - 15%)
```

✅ **Done! Jane is now subscribed to monthly coffee with 15% off!**

---

**Need Help?** Check `SUBSCRIPTION_AUTO_PUSH_COMPLETE.md` for full technical documentation.

