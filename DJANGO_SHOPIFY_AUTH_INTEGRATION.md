# Django Shopify Auth Integration Guide for Lavish Library

## 📋 Overview

**Django Shopify Auth** provides OAuth-based authentication for Shopify apps, allowing Shopify stores to authenticate as "users" in your Django application. This is different from your current Shopify integration which syncs data - this package handles **app authentication and installation**.

---

## 🔑 Key Concepts

### **1. Two Types of Shopify Apps:**

#### **Embedded Apps** (Runs inside Shopify admin)
- Uses session token-based authentication
- Displays within Shopify admin iframe
- Modern approach (required since 2021)
- **NOT supported by this package** - requires separate implementation

#### **Standalone Apps** (Independent web app)
- Traditional OAuth flow
- Runs on your own domain
- Users redirect to your app for features
- **THIS is what django-shopify-auth provides**

### **2. Authentication Flow:**

```
┌─────────────┐     1. Install App      ┌──────────────┐
│   Shopify   │ ───────────────────────> │  Your Django │
│    Store    │                          │     App      │
│   Owner     │                          │              │
└─────────────┘                          └──────────────┘
       │                                         │
       │ 2. Redirect to Shopify OAuth            │
       │ <─────────────────────────────────────  │
       │                                         │
       │ 3. Authorize & Get Access Token         │
       │  ──────────────────────────────────────>│
       │                                         │
       │ 4. Store Token in Database              │
       │                                  ┌──────▼──────┐
       │                                  │  ShopUser   │
       │                                  │  (Database) │
       │                                  └─────────────┘
```

### **3. What This Package Provides:**

✅ **Custom User Model** - `AbstractShopUser` (stores Shopify domain + token)  
✅ **OAuth Backend** - Handles Shopify OAuth handshake  
✅ **Login Views** - `/login/` and `/login/finalize/` endpoints  
✅ **Session Context** - Easy API calls with `with user.session:`  
✅ **Token Persistence** - Access tokens saved in database  
✅ **Decorators** - `@login_required` for Shopify-authenticated views  

---

## 🆚 Your Current Setup vs Django Shopify Auth

### **Current Lavish Library Setup:**

| Feature | Current Status |
|---------|---------------|
| User Model | `CustomUser` (AbstractUser) - Regular Django users |
| Authentication | Username/password, facial recognition, MFA |
| Shopify Integration | Sync orders/products/inventory via API |
| Access Tokens | Stored in environment variables |
| Multi-Store | Not designed for multiple Shopify stores |

### **With Django Shopify Auth:**

| Feature | With Package |
|---------|-------------|
| User Model | `ShopUser` (AbstractShopUser) - Each store is a user |
| Authentication | Shopify OAuth (store owners authenticate) |
| Shopify Integration | Per-store access tokens in database |
| Access Tokens | Unique token per store in database |
| Multi-Store | Built-in - each store has own account |

---

## 🤔 Do You Need This Package?

### **Use Django Shopify Auth If:**

✅ You're building a **public Shopify app** (in the App Store)  
✅ Multiple Shopify stores will install your app  
✅ Each store needs their own account/dashboard  
✅ You want stores to authenticate via OAuth  
✅ Building a standalone app (not embedded in Shopify admin)  

### **DON'T Use Django Shopify Auth If:**

❌ You're building a **private app** for one store only  
❌ Your app is **embedded** in Shopify admin (use session tokens instead)  
❌ You already have access tokens and just need to sync data  
❌ You want to keep your existing user authentication system  

---

## 🎯 Your Current Use Case

Based on your project structure, you have:

1. **Single Shopify Store Integration** (`7fa66c-ac.myshopify.com`)
2. **Existing User System** (customers, staff, companies)
3. **Data Sync Focus** (orders, inventory, payments, subscriptions)
4. **Backend API** for frontend consumption

### **Recommendation:**

**You DON'T need django-shopify-auth** for your current setup because:

- ✅ You're syncing data from **one Shopify store** (not building multi-store app)
- ✅ You have **custom user authentication** (not Shopify OAuth)
- ✅ You're using **admin API tokens** (not per-store OAuth)
- ✅ Your app is **backend-focused** (not a Shopify App Store app)

---

## 📦 How It Would Work (If You Needed It)

### **Installation:**

```bash
pip install django-shopify-auth
```

### **Add to requirements.txt:**

```
django-shopify-auth==1.0.0
```

### **1. Create Shopify Shop User Model:**

```python
# accounts/models.py

from shopify_auth.models import AbstractShopUser

class ShopifyShopUser(AbstractShopUser):
    """
    Custom user model for Shopify stores.
    Each Shopify store that installs your app becomes a 'user'.
    """
    # AbstractShopUser provides:
    # - myshopify_domain (store domain)
    # - token (access token)
    
    # Add custom fields if needed
    store_name = models.CharField(max_length=200, blank=True)
    plan_level = models.CharField(max_length=50, default='basic')
    subscription_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.myshopify_domain
```

### **2. Configure Settings:**

```python
# core/settings.py

# Shopify App Configuration
SHOPIFY_APP_NAME = 'Lavish Library'
SHOPIFY_APP_API_KEY = os.environ.get('SHOPIFY_APP_API_KEY')
SHOPIFY_APP_API_SECRET = os.environ.get('SHOPIFY_APP_API_SECRET')
SHOPIFY_APP_API_SCOPE = [
    'read_products',
    'write_products',
    'read_orders',
    'read_customers',
    'read_inventory',
    'write_subscriptions',
]
SHOPIFY_APP_API_VERSION = "2024-01"
SHOPIFY_APP_DEV_MODE = False  # Set to True for local testing

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'shopify_auth',
]

# Add Shopify Auth Backend
AUTHENTICATION_BACKENDS = (
    'shopify_auth.backends.ShopUserBackend',  # For Shopify stores
    'django.contrib.auth.backends.ModelBackend',  # For regular users
)

# Add context processor
TEMPLATES = [
    {
        # ... existing config ...
        'OPTIONS': {
            'context_processors': [
                # ... existing processors ...
                'shopify_auth.context_processors.shopify_auth',
            ],
        },
    },
]

# Use ShopUser model
AUTH_USER_MODEL = 'accounts.ShopifyShopUser'  # WARNING: Replaces CustomUser!
```

### **3. Add URLs:**

```python
# core/urls.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('shopify/', include('shopify_auth.urls')),  # Adds /shopify/login/
    # ... rest of URLs ...
]
```

### **4. Run Migrations:**

```bash
python manage.py makemigrations
python manage.py migrate
```

### **5. Create Protected Views:**

```python
# views.py

from shopify_auth.decorators import login_required
import shopify

@login_required
def dashboard(request):
    """
    Only accessible after Shopify OAuth.
    request.user is the authenticated Shopify store.
    """
    store_domain = request.user.myshopify_domain
    
    # Make API calls on behalf of this store
    with request.user.session:
        products = shopify.Product.find()
        orders = shopify.Order.find(status='open')
    
    return render(request, 'dashboard.html', {
        'store_domain': store_domain,
        'products': products,
        'orders': orders
    })
```

### **6. Configure Shopify Partner App:**

1. Go to https://partners.shopify.com
2. Create new app
3. Set **App URL**: `https://yourapp.com/`
4. Set **Redirect URL**: `https://yourapp.com/shopify/login/finalize/`
5. Set **Scopes**: Match `SHOPIFY_APP_API_SCOPE` in settings
6. Get API Key and Secret, add to environment variables

---

## ⚠️ Important Considerations

### **1. User Model Conflict:**

**Problem:** Django only allows ONE user model per project.

Your current setup:
```python
AUTH_USER_MODEL = 'accounts.CustomUser'  # Regular users
```

Django Shopify Auth requires:
```python
AUTH_USER_MODEL = 'accounts.ShopifyShopUser'  # Shopify stores
```

**You can't have both!**

### **Solution Options:**

#### **Option A: Dual Model Approach** (Recommended if needed)
```python
# Keep CustomUser for regular users
class CustomUser(AbstractUser):
    # ... your existing fields ...
    pass

# Add ShopUser for Shopify stores (separate model, NOT user model)
class ShopifyStore(models.Model):
    myshopify_domain = models.CharField(max_length=255, unique=True)
    access_token = models.CharField(max_length=255)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # ... other store fields ...

# Don't change AUTH_USER_MODEL
```

#### **Option B: Manual OAuth** (What you're currently doing)
- Store API tokens in environment/database
- Handle OAuth manually via Shopify API
- Keep your existing user model
- **This is what you're already doing!**

---

## 🚀 Alternative: Manual Shopify OAuth (Current Approach)

Your current approach is actually better for your use case:

### **What You Have:**

```python
# Environment variable (or database)
SHOPIFY_ADMIN_API_TOKEN = 'shpat_xxxxx'

# Sync data from one store
from shopify_integration.admin import sync_orders, sync_products

# Make API calls
import shopify
shopify.ShopifyResource.set_site(
    f"https://{SHOPIFY_API_KEY}:{SHOPIFY_PASSWORD}@{SHOPIFY_SHOP_DOMAIN}/admin"
)
products = shopify.Product.find()
```

### **Benefits of Your Approach:**

✅ **Simpler** - No complex OAuth flow  
✅ **Single Store** - Perfect for private app  
✅ **Keep CustomUser** - No user model conflicts  
✅ **Direct API Access** - Tokens stored securely  
✅ **Backend Focus** - API for frontend consumption  

---

## 📊 Comparison Summary

| Aspect | Django Shopify Auth | Your Current Setup |
|--------|--------------------|--------------------|
| **Use Case** | Multi-store public app | Single-store private app |
| **Authentication** | OAuth per store | Admin API token |
| **User Model** | AbstractShopUser | CustomUser |
| **Token Storage** | Database per store | Environment/settings |
| **Complexity** | High | Low |
| **Best For** | App Store apps | Private integrations |

---

## 🎯 Recommendation for Lavish Library

### **KEEP YOUR CURRENT APPROACH**

You're already doing it right! Your setup is:

✅ **Appropriate** for single-store integration  
✅ **Simpler** than full OAuth  
✅ **Compatible** with your existing user system  
✅ **Sufficient** for data sync requirements  

### **When to Consider Django Shopify Auth:**

Only if you plan to:
1. Build a **public Shopify app** for the App Store
2. Let **multiple stores** install your app
3. Each store needs **separate account/dashboard**
4. Sell your app as a **subscription service**

---

## 📝 Current Integration is Fine

Your existing Shopify integration is working well:

```python
# ✅ What you have (good for your case)
shopify_integration/
  ├── models.py          # Webhook subscriptions
  ├── admin.py           # Sync orders/inventory
  └── graphql_client.py  # API calls

# Settings
SHOPIFY_SHOP_DOMAIN = '7fa66c-ac.myshopify.com'
SHOPIFY_ADMIN_API_TOKEN = os.getenv('SHOPIFY_ADMIN_API_TOKEN')
```

**This is the correct approach for your project!**

---

## 🔧 If You Must Implement Multi-Store Support

If you later need multi-store support WITHOUT changing your user model:

```python
# Create a separate Store model
class ShopifyStore(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    access_token = models.CharField(max_length=255)
    shop_name = models.CharField(max_length=200)
    email = models.EmailField()
    
    # Link to existing user system
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    is_active = models.BooleanField(default=True)
    scopes = models.JSONField(default=list)
    installed_at = models.DateTimeField(auto_now_add=True)

# Create OAuth views manually
def shopify_oauth_begin(request):
    # Build Shopify OAuth URL
    # Redirect user to Shopify for authorization
    pass

def shopify_oauth_callback(request):
    # Receive OAuth callback
    # Exchange code for access token
    # Save to ShopifyStore model
    pass
```

This gives you multi-store support WITHOUT replacing your user model!

---

## 📚 Resources

- **Django Shopify Auth**: https://github.com/shopify/django-shopify-auth
- **Shopify OAuth Docs**: https://shopify.dev/docs/apps/auth/oauth
- **Your Current Integration**: `shopify_integration/` app ✅
- **Skip System**: `skips/` app (working perfectly!)

---

## ✅ Summary

**For Lavish Library:**

- ❌ **Don't install** `django-shopify-auth`
- ✅ **Keep your current** Shopify integration
- ✅ **Your setup is correct** for single-store private app
- ✅ **Focus on** data sync and skip functionality
- 💡 **Consider OAuth** only if going multi-store public

**Your current architecture is exactly right for your use case!**
