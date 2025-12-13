# Deploying Your Custom Lavish Frontend - Complete Guide

**Date:** December 13, 2025  
**Project:** Lavish Library Custom Shopify Frontend

---

## 🎯 UNDERSTANDING YOUR CURRENT SETUP

### **What You Have:**
1. **Custom Liquid Theme** (`app/lavish_frontend/`)
   - Enhanced account pages (`enhanced-account.liquid`)
   - Subscription purchase options (`subscription-purchase-options.liquid`)
   - Custom product pages (`main-product.liquid`)
   - Custom assets (JS, CSS)

2. **Django Backend** (`app/lavish_backend/`)
   - REST API for customer data
   - Subscription management
   - Order processing
   - Location services

3. **Integration Layer**
   - `django-integration.js` - Connects frontend to backend
   - CORS configured for cross-origin requests
   - API endpoints at your Django server

---

## 📋 DEPLOYMENT SCENARIOS

---

## **SCENARIO 1: DEPLOY AS SHOPIFY THEME (RECOMMENDED)**

### ✅ **Best For:**
- Maintaining Shopify's infrastructure
- Using Shopify Checkout
- Leveraging Shopify CDN
- Minimal hosting costs
- Built-in SSL/Security
- PCI compliance for payments

### 📦 **What This Means:**
Your custom Liquid files become the **active theme** on your Shopify store. Customers see your custom design, but still use Shopify's checkout and infrastructure.

---

### **STEP-BY-STEP IMPLEMENTATION:**

#### **Phase 1: Prepare Your Theme for Production**

**1. Theme Structure Validation**
```
lavish_frontend/
├── assets/
│   ├── django-integration.js ✅
│   ├── enhanced-account.js ✅
│   ├── application.css
│   └── theme.js
├── config/
│   └── settings_schema.json
├── layout/
│   └── theme.liquid
├── sections/
│   ├── enhanced-account.liquid ✅
│   ├── main-product.liquid ✅
│   └── main-cart-items.liquid
├── snippets/
│   └── subscription-purchase-options.liquid ✅
└── templates/
    ├── index.json
    ├── product.json
    └── customers/
        └── account.json (must point to enhanced-account section)
```

**2. Update API Endpoints for Production**

Edit `assets/django-integration.js`:
```javascript
// CHANGE FROM:
const API_BASE_URL = 'http://localhost:8000';

// TO:
const API_BASE_URL = 'https://api.lavishlibrary.com.au'; // Your production Django URL
```

**3. Configure CORS on Django Backend**

Edit `app/lavish_backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'https://lavishlibrary.com.au',
    'https://www.lavishlibrary.com.au',
    'https://7fa66c-ac.myshopify.com',  # Your Shopify admin domain
]

# For production
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    'https://lavishlibrary.com.au',
    'https://www.lavishlibrary.com.au',
]
```

---

#### **Phase 2: Deploy Theme to Shopify**

**METHOD A: Using Shopify CLI (Development → Production)**

**1. Install Shopify CLI** (if not already installed):
```bash
npm install -g @shopify/cli@latest
```

**2. Authenticate with Your Store:**
```bash
cd app/lavish_frontend
shopify auth login
```

**3. Push Theme to Shopify:**
```bash
# Push to a new unpublished theme (for testing)
shopify theme push --unpublished

# OR push and publish immediately
shopify theme push --publish

# OR push to specific theme
shopify theme push --theme="Lavish Custom Theme"
```

**4. Preview Before Publishing:**
```bash
# Get theme ID
shopify theme list

# Share preview link
shopify theme share --theme=<THEME_ID>
```

**METHOD B: Using Theme Kit (Legacy)**

**1. Install Theme Kit:**
```bash
brew install themekit  # Mac
choco install themekit # Windows
```

**2. Configure:**
```bash
cd app/lavish_frontend
theme configure --password=[your-private-app-password] --store=[your-store.myshopify.com] --themeid=[theme-id]
```

**3. Deploy:**
```bash
theme deploy
```

**METHOD C: Manual Upload via Shopify Admin**

1. **Zip Your Theme:**
   - Compress entire `lavish_frontend` folder
   - Ensure structure is correct (no parent folder)

2. **Upload to Shopify:**
   - Go to: `Shopify Admin → Online Store → Themes`
   - Click: "Add theme" → "Upload zip file"
   - Select your zipped theme
   - Wait for processing

3. **Preview & Publish:**
   - Click "Customize" to preview
   - Click "Actions" → "Publish" when ready

---

#### **Phase 3: Deploy Django Backend**

**OPTION A: Deploy to AWS EC2/DigitalOcean**

**1. Server Setup:**
```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip nginx postgresql redis

# Clone your repo
git clone https://github.com/eo-nwanze/lavish.git
cd lavish/app/lavish_backend

# Install Python packages
pip install -r requirements.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=core.settings
export SHOPIFY_API_KEY=your_key
export SHOPIFY_ACCESS_TOKEN=your_token
export DATABASE_URL=postgresql://...
```

**2. Configure Gunicorn:**
```bash
# Install
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/lavish-backend.service
```

```ini
[Unit]
Description=Lavish Backend Django App
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/lavish/app/lavish_backend
Environment="PATH=/home/ubuntu/lavish/venv/bin"
ExecStart=/home/ubuntu/lavish/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 core.wsgi:application

[Install]
WantedBy=multi-user.target
```

**3. Configure Nginx:**
```nginx
server {
    listen 80;
    server_name api.lavishlibrary.com.au;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/lavish/app/lavish_backend/staticfiles/;
    }
}
```

**4. Setup SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.lavishlibrary.com.au
```

**5. Start Services:**
```bash
sudo systemctl start lavish-backend
sudo systemctl enable lavish-backend
sudo systemctl restart nginx
```

**OPTION B: Deploy to Heroku (Simpler)**

**1. Install Heroku CLI:**
```bash
brew install heroku/brew/heroku  # Mac
# Or download from heroku.com
```

**2. Create App:**
```bash
cd app/lavish_backend
heroku create lavish-backend-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis
heroku addons:create heroku-redis:mini
```

**3. Configure Environment:**
```bash
heroku config:set DJANGO_SETTINGS_MODULE=core.settings
heroku config:set SECRET_KEY=your_secret_key
heroku config:set SHOPIFY_API_KEY=your_key
heroku config:set SHOPIFY_ACCESS_TOKEN=your_token
heroku config:set ALLOWED_HOSTS=lavish-backend-api.herokuapp.com,api.lavishlibrary.com.au
```

**4. Create Procfile:**
```
web: gunicorn core.wsgi --log-file -
worker: celery -A core worker -l info
```

**5. Deploy:**
```bash
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

**OPTION C: Deploy to Railway (Modern Alternative)**

**1. Connect GitHub:**
- Visit railway.app
- Click "New Project" → "Deploy from GitHub"
- Select your repository

**2. Configure:**
- Add PostgreSQL database
- Add Redis instance
- Set environment variables in dashboard

**3. Auto-deploys** on every push to main branch

---

#### **Phase 4: Configure Custom Domain**

**1. DNS Setup:**

Add these records to your domain registrar (GoDaddy, Namecheap, etc.):

```
Type    Host    Value                           TTL
A       @       23.227.38.65 (Shopify IP)       1 hour
A       www     23.227.38.65 (Shopify IP)       1 hour
CNAME   api     your-server.com                 1 hour
```

**2. Add Domain to Shopify:**
- Go to: `Shopify Admin → Online Store → Domains`
- Click "Connect existing domain"
- Enter: `lavishlibrary.com.au` and `www.lavishlibrary.com.au`
- Follow verification steps

**3. Enable SSL:**
- Shopify automatically provisions SSL for your custom domain
- Wait 24-48 hours for full propagation

---

#### **Phase 5: Testing Checklist**

**Frontend Tests:**
```
✅ Homepage loads with custom theme
✅ Product pages show subscription options
✅ Enhanced account page accessible
✅ Tab navigation works (Orders, Subscriptions, etc.)
✅ Address forms load country/state/city data
✅ Subscription options display on eligible products
✅ Add to cart works for both one-time and subscriptions
✅ Checkout process completes successfully
```

**Backend API Tests:**
```bash
# Test API connectivity
curl https://api.lavishlibrary.com.au/api/health/

# Test locations endpoint
curl https://api.lavishlibrary.com.au/api/locations/countries/

# Test CORS
curl -H "Origin: https://lavishlibrary.com.au" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://api.lavishlibrary.com.au/api/locations/countries/
```

**Integration Tests:**
```
✅ Django API accessible from Shopify domain
✅ CORS headers present in responses
✅ Customer data syncs between Shopify and Django
✅ Orders sync bidirectionally
✅ Subscriptions sync bidirectionally
✅ Webhooks fire correctly
```

---

## **SCENARIO 2: HEADLESS SHOPIFY WITH CUSTOM FRONTEND**

### ✅ **Best For:**
- Complete design control
- Custom routing/navigation
- App-like experience
- Multiple sales channels
- Advanced customization

### ⚠️ **Limitations:**
- Must build custom checkout (complex)
- Higher hosting costs
- More maintenance
- Need to implement PCI compliance
- No Shopify checkout features

---

### **IMPLEMENTATION:**

**1. Use Shopify Storefront API**

Your frontend makes GraphQL requests directly to Shopify:

```javascript
const STOREFRONT_ACCESS_TOKEN = 'your_storefront_token';
const SHOP_DOMAIN = '7fa66c-ac.myshopify.com';

async function fetchProducts() {
  const response = await fetch(
    `https://${SHOP_DOMAIN}/api/2024-01/graphql.json`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Storefront-Access-Token': STOREFRONT_ACCESS_TOKEN,
      },
      body: JSON.stringify({
        query: `
          query {
            products(first: 20) {
              edges {
                node {
                  id
                  title
                  sellingPlanGroups(first: 5) {
                    edges {
                      node {
                        name
                        sellingPlans(first: 10) {
                          edges {
                            node {
                              id
                              name
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        `,
      }),
    }
  );
  return await response.json();
}
```

**2. Host Frontend Separately**

Options:
- **Vercel** (Next.js recommended)
- **Netlify** (Static sites)
- **AWS S3 + CloudFront** (Static)
- **Your own server** (Any framework)

**3. Implement Custom Checkout**

```javascript
// Create checkout with subscription
async function createCheckout(variantId, sellingPlanId) {
  const mutation = `
    mutation checkoutCreate($input: CheckoutCreateInput!) {
      checkoutCreate(input: $input) {
        checkout {
          id
          webUrl
          lineItems(first: 5) {
            edges {
              node {
                title
                quantity
              }
            }
          }
        }
        checkoutUserErrors {
          code
          field
          message
        }
      }
    }
  `;

  const variables = {
    input: {
      lineItems: [{
        variantId: variantId,
        quantity: 1,
        sellingPlanId: sellingPlanId  // Include for subscription
      }]
    }
  };

  // Make request to Storefront API
  // Redirect to checkout.webUrl
}
```

**NOT RECOMMENDED** for your use case due to complexity.

---

## **SCENARIO 3: HYBRID APPROACH (BEST OF BOTH WORLDS)**

### ✅ **Recommended Configuration**

**What It Is:**
- Shopify theme for main storefront (Scenario 1)
- Django backend for enhanced features
- Custom account dashboard
- Shopify checkout for payments

---

### **ARCHITECTURE:**

```
Customer Browser
       |
       v
[Shopify Theme (Liquid)]
       |
       +---> Shopify Checkout (subscriptions, one-time)
       |
       +---> Django API (account features, data)
              |
              +---> PostgreSQL (customer data, analytics)
              |
              +---> Shopify Admin API (sync)
```

---

### **IMPLEMENTATION DETAILS:**

**1. Theme Structure:**

```liquid
<!-- layout/theme.liquid -->
<!doctype html>
<html>
<head>
  <title>{{ page_title }}</title>
  {{ content_for_header }}
  
  <!-- Your custom assets -->
  <link rel="stylesheet" href="{{ 'application.css' | asset_url }}">
  <script src="{{ 'django-integration.js' | asset_url }}" defer></script>
</head>
<body>
  {{ content_for_layout }}
</body>
</html>
```

**2. Customer Account Template:**

```json
// templates/customers/account.json
{
  "sections": {
    "main": {
      "type": "enhanced-account"
    }
  },
  "order": ["main"]
}
```

**3. Product Template with Subscriptions:**

```json
// templates/product.json
{
  "sections": {
    "main": {
      "type": "main-product",
      "settings": {
        "enable_subscriptions": true
      }
    }
  }
}
```

---

## **PRODUCTION DEPLOYMENT CHECKLIST**

### **Pre-Launch:**

#### **Backend:**
```
✅ Environment variables set
✅ Database migrations run
✅ Static files collected
✅ SSL certificate installed
✅ CORS configured correctly
✅ Webhooks registered with Shopify
✅ API rate limiting enabled
✅ Error logging configured (Sentry)
✅ Backup strategy in place
✅ Django admin secured
```

#### **Frontend (Theme):**
```
✅ API endpoints point to production
✅ All assets uploaded
✅ Theme validated (no errors)
✅ Mobile responsive
✅ Browser compatibility tested
✅ Page speed optimized
✅ SEO meta tags in place
✅ Analytics tracking added
✅ Favicon set
✅ 404 page customized
```

#### **Shopify Configuration:**
```
✅ Products published to Online Store
✅ Selling plans active
✅ Payment gateway configured
✅ Shipping rates set up
✅ Taxes configured
✅ Email notifications customized
✅ Legal pages added (Privacy, Terms, Refunds)
✅ Custom domain connected
✅ Store password removed (launch)
```

#### **Testing:**
```
✅ Test orders (both subscription and one-time)
✅ Customer account creation
✅ Password reset flow
✅ Address management
✅ Subscription management
✅ Order cancellation
✅ Payment processing
✅ Email notifications
✅ Webhook delivery
✅ Mobile experience
```

---

## **MONITORING & MAINTENANCE**

### **Backend Monitoring:**

**1. Setup Monitoring Tools:**
```bash
pip install sentry-sdk django-prometheus

# In settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    environment="production"
)
```

**2. Log Management:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/lavish/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    },
}
```

**3. Automated Backups:**
```bash
# Cron job for database backups
0 2 * * * pg_dump lavish_db | gzip > /backups/lavish_$(date +\%Y\%m\%d).sql.gz
```

### **Performance Optimization:**

**1. Enable Django Caching:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

**2. Shopify Theme Optimization:**
- Minify CSS/JS
- Optimize images (WebP format)
- Lazy load images
- Use Shopify CDN for assets

---

## **COST ESTIMATES**

### **Option 1: Minimal Setup**
```
Shopify Basic Plan:          $39/month
DigitalOcean Droplet:        $12/month
Domain:                      $15/year
SSL:                         FREE (Let's Encrypt)
TOTAL:                       ~$52/month
```

### **Option 2: Standard Setup**
```
Shopify Plan:                $105/month
AWS EC2 (t3.medium):         $35/month
RDS PostgreSQL:              $20/month
Domain + Email:              $30/year
TOTAL:                       ~$163/month
```

### **Option 3: Enterprise Setup**
```
Shopify Plus:                $2000/month
AWS Full Stack:              $300/month
Cloudflare Enterprise:       $200/month
Monitoring (Datadog):        $100/month
TOTAL:                       ~$2600/month
```

---

## **RECOMMENDED APPROACH FOR YOUR STORE**

Based on your current setup, I recommend:

### **Phase 1: Initial Launch** (Weeks 1-2)
1. ✅ Deploy Django backend to DigitalOcean/Heroku
2. ✅ Configure production API endpoints
3. ✅ Push Liquid theme to Shopify
4. ✅ Test on staging theme first
5. ✅ Connect custom domain
6. ✅ Remove store password and launch

### **Phase 2: Optimization** (Month 2)
1. Setup monitoring (Sentry, LogRocket)
2. Implement caching
3. Optimize images and assets
4. Add advanced analytics
5. Setup automated backups

### **Phase 3: Scale** (Month 3+)
1. Add CDN for API if needed
2. Implement rate limiting
3. Add advanced features
4. A/B testing for conversions
5. Customer feedback integration

---

## **SUPPORT RESOURCES**

### **Documentation:**
- Shopify Theme Development: https://shopify.dev/docs/themes
- Storefront API: https://shopify.dev/docs/api/storefront
- Admin API: https://shopify.dev/docs/api/admin
- Liquid Reference: https://shopify.dev/docs/api/liquid

### **Tools:**
- Shopify CLI: https://shopify.dev/docs/themes/tools/cli
- Theme Inspector: Chrome extension for debugging
- GraphiQL: Test GraphQL queries
- Postman: Test API endpoints

---

## **CONCLUSION**

For your Lavish Library store, **Scenario 1 (Shopify Theme)** is the best choice:

✅ Maintains Shopify's robust infrastructure  
✅ Uses Shopify Checkout (PCI compliant)  
✅ Integrates your custom Django backend for enhanced features  
✅ Cost-effective and scalable  
✅ Easy to maintain  

Your enhanced Liquid frontend becomes your live store, customers see your custom design, and everything "just works" while leveraging Shopify's proven e-commerce platform.

---

**Next Steps:**
1. Deploy Django backend to production server
2. Update API endpoints in `django-integration.js`
3. Push theme to Shopify using CLI
4. Test thoroughly on staging theme
5. Publish and launch! 🚀

