# Shopify Customer Access to enhanced-account.liquid

## ✅ YES - Shopify Customers CAN Access enhanced-account.liquid

### **How It Works:**

When a customer account is created on Shopify, that customer can access the `enhanced-account.liquid` page automatically through Shopify's built-in customer authentication system.

---

## 🔐 Shopify Customer Authentication Flow

### **1. Customer Account Creation:**

**Three Ways Customers Get Created:**

#### **A. Self-Registration** (`/account/register`)
```
Customer visits: yourstore.com/account/register
↓
Fills out: Email, First Name, Last Name, Password
↓
Shopify creates customer account
↓
Customer receives activation email (if enabled)
↓
Customer can log in
```

#### **B. Admin Creation** (Shopify Admin Dashboard)
```
Store owner: Shopify Admin → Customers → Add Customer
↓
Fills out customer details
↓
Option: Send account activation email
↓
Customer receives invitation to set password
↓
Customer can log in
```

#### **C. Checkout Account Creation**
```
Guest checkout with email
↓
Shopify creates customer record
↓
After order: "Create account" option appears
↓
Customer sets password
↓
Customer can log in
```

---

## 🚪 Accessing enhanced-account.liquid

### **URL Structure:**

```
https://7fa66c-ac.myshopify.com/account
```

This URL automatically loads: `templates/customers/account.json`

Which renders: `sections/enhanced-account.liquid`

### **Authentication Check:**

Shopify **automatically protects** customer account pages. Here's how:

```liquid
{# templates/customers/account.json renders enhanced-account section #}

{# In enhanced-account.liquid: #}
<script>
  const customerId = {{ customer.id | json }};  {# ← Shopify provides customer object #}
</script>

<h3>{{ customer.first_name | default: 'My' }} Account</h3>
```

**The `customer` object is ONLY available when:**
- ✅ Customer is logged in
- ✅ Valid session cookie exists
- ✅ Accessing `/account` URL

**If not logged in:**
- ❌ Shopify redirects to `/account/login`
- ❌ `customer` object is `nil`

---

## 🔑 Customer Object Properties

When a Shopify customer accesses `enhanced-account.liquid`, they have access to:

```liquid
{{ customer.id }}                  {# Shopify customer ID #}
{{ customer.email }}               {# Email address #}
{{ customer.first_name }}          {# First name #}
{{ customer.last_name }}           {# Last name #}
{{ customer.name }}                {# Full name #}
{{ customer.phone }}               {# Phone number #}
{{ customer.accepts_marketing }}   {# Marketing consent #}
{{ customer.orders_count }}        {# Total orders #}
{{ customer.total_spent }}         {# Total spent #}
{{ customer.tags }}                {# Customer tags #}
{{ customer.default_address }}     {# Default address object #}
{{ customer.addresses }}           {# All addresses #}
{{ customer.has_account }}         {# Has account (true) #}
```

---

## 🛡️ Security & Access Control

### **What Shopify Handles Automatically:**

✅ **Authentication** - Checks if customer is logged in  
✅ **Session Management** - Cookie-based sessions  
✅ **Password Protection** - Hashed passwords  
✅ **Account Recovery** - Forgot password flow  
✅ **Email Verification** - Optional email verification  
✅ **URL Protection** - `/account/*` routes require login  

### **What Your Theme Can Access:**

```liquid
{# In enhanced-account.liquid - These work automatically: #}

{% if customer %}
  <p>Welcome, {{ customer.first_name }}!</p>
  
  {# Show orders #}
  {% for order in customer.orders %}
    <p>Order #{{ order.name }} - {{ order.total_price | money }}</p>
  {% endfor %}
  
  {# Show addresses #}
  {% for address in customer.addresses %}
    <p>{{ address.address1 }}, {{ address.city }}</p>
  {% endfor %}
{% else %}
  <p>Please <a href="/account/login">log in</a></p>
{% endif %}
```

---

## 🔗 Customer Account URLs

### **Public URLs (No Login Required):**

| URL | Purpose | Template |
|-----|---------|----------|
| `/account/register` | Create account | `templates/customers/register.json` |
| `/account/login` | Login page | `templates/customers/login.json` |
| `/account/recover` | Forgot password | `templates/customers/reset_password.json` |

### **Protected URLs (Login Required):**

| URL | Purpose | Template |
|-----|---------|----------|
| `/account` | Account dashboard | `templates/customers/account.json` → `enhanced-account.liquid` |
| `/account/addresses` | Manage addresses | `templates/customers/addresses.json` |
| `/account/orders/:id` | View order details | `templates/customers/order.json` |

---

## 📊 Your Current Setup

### **File Structure:**

```
lavish_frontend/
├── templates/
│   └── customers/
│       ├── account.json          ← Entry point for /account
│       ├── login.json             ← Login page
│       ├── register.json          ← Registration
│       └── addresses.json         ← Address management
└── sections/
    └── enhanced-account.liquid    ← Your custom account dashboard
```

### **account.json Configuration:**

```json
{
  "sections": {
    "main": {
      "type": "enhanced-account",
      "settings": {
        "padding_top": 36,
        "padding_bottom": 36
      }
    }
  },
  "order": ["main"]
}
```

This tells Shopify: "When someone accesses `/account`, render the `enhanced-account` section"

---

## 🧪 Testing Customer Access

### **Test 1: Create Test Customer**

**Via Shopify Admin:**
```
1. Shopify Admin → Customers → Add customer
2. Fill in:
   - First name: Test
   - Last name: Customer
   - Email: test@example.com
3. Check: "Send account invite email"
4. Click "Save"
```

**Customer receives email:**
```
Subject: Complete your account setup for Lavish Library

Hi Test,

Click here to activate your account and set your password:
[Activate Account Button]
```

### **Test 2: Customer Login**

```
1. Customer clicks activation link
2. Sets password
3. Redirected to /account
4. enhanced-account.liquid loads with customer data
```

### **Test 3: Verify Access**

**Browser Console:**
```javascript
console.log(customerId);  // Should show Shopify customer ID
```

**If not logged in:**
```
Automatic redirect to: /account/login
```

---

## 🔄 Customer Data Flow

### **When Customer Visits /account:**

```
┌─────────────────┐
│  Customer visits │
│  /account URL    │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Shopify checks      │
│ session cookie      │
└────────┬────────────┘
         │
    ┌────┴────┐
    │ Logged  │
    │   in?   │
    └────┬────┘
         │
    Yes  │  No
    ┌────┴────┐
    ▼         ▼
┌─────────┐  ┌──────────────┐
│ Load    │  │ Redirect to  │
│ account │  │ /account/    │
│ .json   │  │ login        │
└────┬────┘  └──────────────┘
     │
     ▼
┌─────────────────────┐
│ Render enhanced-    │
│ account.liquid with │
│ customer object     │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ JavaScript loads:   │
│ - Orders from API   │
│ - Subscriptions     │
│ - Payment methods   │
└─────────────────────┘
```

---

## 🎯 Key Points for Lavish Library

### **1. Shopify Handles Authentication**

You **don't need to build** login/authentication. Shopify provides:
- ✅ Login page at `/account/login`
- ✅ Registration at `/account/register`
- ✅ Password reset at `/account/recover`
- ✅ Session management
- ✅ Cookie handling

### **2. Customer Object is Automatic**

When logged in, `customer` object is **automatically available** in:
- ✅ All `/account/*` pages
- ✅ Your `enhanced-account.liquid` section
- ✅ All customer templates

### **3. Your Backend Integration**

Your Django backend API calls work alongside Shopify auth:

```javascript
// In enhanced-account.liquid JavaScript:

// Shopify customer ID is available
const customerId = {{ customer.id | json }};

// Make API calls to your Django backend
fetch(`/api/skips/subscriptions/?shopify_customer_id=${customerId}`)
  .then(response => response.json())
  .then(data => {
    // Display customer's subscriptions
    console.log(data.subscriptions);
  });
```

### **4. No Conflict with Your Django User System**

These are **separate systems**:

| System | Purpose | Users |
|--------|---------|-------|
| **Shopify Customers** | Store customers who buy products | Shopping, orders, subscriptions |
| **Django CustomUser** | Internal admin/staff users | Backend management, admin dashboard |

They can coexist peacefully!

---

## 🔐 Security Considerations

### **What's Protected:**

✅ `/account` - Only accessible when logged in  
✅ `/account/orders` - Customer's own orders only  
✅ `/account/addresses` - Customer's own addresses only  
✅ `{{ customer.id }}` - Current logged-in customer only  

### **What's NOT Automatically Protected:**

⚠️ **Your Django API Endpoints**

```javascript
// This call works even if not logged into Shopify:
fetch('/api/skips/subscriptions/?shopify_customer_id=12345')
```

**Solution:** Add authentication to your Django API:

```python
# skips/views.py

from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def subscription_details(request, subscription_id):
    # Add authentication check
    shopify_customer_id = request.GET.get('shopify_customer_id')
    
    # Verify the request is coming from authenticated Shopify customer
    # (check session, token, or Shopify API verification)
    
    subscription = get_object_or_404(
        CustomerSubscription,
        shopify_subscription_contract_id=subscription_id,
        shopify_customer_id=shopify_customer_id  # Match customer
    )
    
    return json_response({...})
```

---

## 🧪 Complete Test Flow

### **Step 1: Create Customer Account**

```
Method 1: Self-Registration
→ Go to: https://7fa66c-ac.myshopify.com/account/register
→ Fill in: Email, First Name, Last Name, Password
→ Click: Create Account
→ (Optional) Verify email

Method 2: Admin Creation
→ Shopify Admin → Customers → Add customer
→ Check: "Send account invite email"
→ Customer receives activation link
```

### **Step 2: Customer Logs In**

```
→ Go to: https://7fa66c-ac.myshopify.com/account/login
→ Enter: Email & Password
→ Click: Sign In
→ Redirected to: /account
```

### **Step 3: enhanced-account.liquid Loads**

```
URL: /account
↓
Renders: templates/customers/account.json
↓
Loads section: enhanced-account.liquid
↓
Customer object available:
  - customer.id
  - customer.first_name
  - customer.email
  - customer.orders
  - etc.
```

### **Step 4: Verify JavaScript Works**

```javascript
// Browser console should show:
console.log(customerId);  // e.g., 7380041244860

// API calls should work:
fetch(`/api/skips/subscriptions/?shopify_customer_id=${customerId}`)
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## ✅ Summary

### **Question: Can Shopify customers access enhanced-account.liquid?**

**Answer: YES! ✅**

### **How:**

1. **Customer creates account** (self-register or admin-created)
2. **Customer logs in** at `/account/login`
3. **Shopify authenticates** and creates session
4. **Customer accesses** `/account`
5. **Shopify renders** `enhanced-account.liquid`
6. **Customer object available** with all customer data
7. **Your JavaScript loads** subscriptions, orders, etc. via API

### **No Additional Setup Needed:**

✅ Shopify handles authentication automatically  
✅ Customer object is provided by Shopify  
✅ Your enhanced-account.liquid just works  
✅ Django API can query by `customer.id`  

### **What You Need to Do:**

1. ✅ **Nothing for basic access** - it already works!
2. ⏳ **Add API authentication** - Verify Django endpoints check customer ID
3. ⏳ **Test with real customers** - Create test accounts and verify
4. ⏳ **Handle edge cases** - What if customer has no subscriptions yet?

---

## 🎉 Your Setup is Ready!

**Your enhanced-account.liquid is already accessible to Shopify customers!** Any customer who:
- Creates an account via `/account/register`
- Gets invited by admin
- Checks out and creates account

...can immediately access `/account` and see your beautiful custom dashboard with subscriptions, orders, and skip functionality! 🚀
