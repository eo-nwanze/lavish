# COMPREHENSIVE HYBRID INTEGRATION GUIDE
## Lavish Library + Shopify - Production Deployment

**Date:** December 13, 2025  
**Objective:** Deploy hybrid system without breaking any functionality  
**Architecture:** Shopify Theme (Frontend) + Django Backend + Shopify Checkout

---

## 📊 EXECUTIVE SUMMARY

### What You'll Have After This Guide:

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐          ┌──────────────────┐
│   CUSTOMER       │          │   SHOPIFY CDN    │
│   BROWSER        │◄─────────┤   (Theme Files)  │
└────────┬─────────┘          └──────────────────┘
         │
         ├──────────────────► Shopify Checkout (Payments)
         │
         ├──────────────────► Django Backend API
         │                    (Customer Data, Subscriptions)
         │
         └──────────────────► Shopify Admin API
                              (Products, Orders)

BENEFITS:
✅ Shopify handles all payments (PCI compliant)
✅ Django manages custom business logic
✅ Fast CDN delivery for theme assets
✅ Custom account dashboard
✅ Advanced subscription management
```

---

## 🎯 PART 1: WHAT YOU NEED TO PROVIDE

### A. Shopify Store Information

#### 1. **Store URL** ✅ (You already have this)
```
Current: 7fa66c-ac.myshopify.com
Custom Domain: [Your custom domain if you have one]
```

**Action Required:** None - already configured

#### 2. **Shopify API Credentials** ✅ (You already have these)

Check if these are set in your `.env` file:
```env
SHOPIFY_STORE_URL=7fa66c-ac.myshopify.com
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_ACCESS_TOKEN=your_access_token_here
SHOPIFY_API_VERSION=2025-01
```

**Action Required:**
- [ ] Verify these values exist in your `.env` file (root of project)
- [ ] If missing, I'll show you how to get them (Section B)

#### 3. **Shopify App Scopes Required**

Your app needs these permissions:
- ✅ `read_products, write_products`
- ✅ `read_customers, write_customers`
- ✅ `read_orders, write_orders`
- ✅ `read_own_subscription_contracts, write_own_subscription_contracts`
- ✅ `read_customer_payment_methods` (read-only)
- ⚠️ `read_locations` (for multi-location support)

**Action Required:**
- [ ] Provide current app scopes (from Shopify Admin)
- [ ] Or I'll guide you to check/update them

---

### B. Hosting Information for Django Backend

#### Option 1: Existing Server (You mentioned: lavish-backend.endevops.net)

**Current Status:** ✅ You already have backend deployed at `https://lavish-backend.endevops.net`

**Action Required:**
- [ ] Confirm this server is running
- [ ] Confirm Django is accessible at this URL
- [ ] Provide server access method (SSH, FTP, control panel)
- [ ] Confirm database type (PostgreSQL/MySQL/SQLite)

#### Option 2: New Server Setup

If you need to set up a new server:

**Checklist:**
- [ ] Server provider (AWS, DigitalOcean, Heroku, etc.)
- [ ] Server OS (Ubuntu 22.04 recommended)
- [ ] Python version (3.10+ required)
- [ ] Database (PostgreSQL recommended)
- [ ] Domain name for API (e.g., `api.lavishlibrary.com.au`)
- [ ] SSL certificate (Let's Encrypt recommended)

---

### C. Domain & DNS Information

#### 1. **Custom Domain** (Optional but recommended)

**Current Shopify Domain:** `7fa66c-ac.myshopify.com`

**Custom Domain Examples:**
- Main store: `lavishlibrary.com.au`
- API backend: `api.lavishlibrary.com.au`

**Action Required:**
- [ ] Do you have a custom domain? (Yes/No)
- [ ] If yes, provide domain name
- [ ] Provide DNS provider (Cloudflare, Route53, Namecheap, etc.)
- [ ] DNS management access (for configuration)

#### 2. **SSL Certificates**

**For Shopify Store:** ✅ Automatic (Shopify provides)
**For Django Backend:** ⚠️ Need to configure

**Action Required:**
- [ ] Confirm backend has SSL/HTTPS enabled
- [ ] If not, I'll guide you through Let's Encrypt setup

---

### D. Theme Files Location

**Current Status:** ✅ You have two theme directories:
- `app/crave_theme/` - Current working theme with fixes
- `app/lavish_frontend/` - Enhanced account pages

**Action Required:**
- [ ] Confirm which theme should be deployed to production
- [ ] Recommendation: Use `crave_theme` (has the checkout fixes)
- [ ] Or: Merge enhanced features from lavish_frontend into crave_theme

---

### E. Environment Variables Checklist

Create/update `.env` file in project root:

```env
# === DJANGO SETTINGS ===
DEBUG=False
SECRET_KEY=your-production-secret-key-here-min-50-chars
ALLOWED_HOSTS=lavish-backend.endevops.net,api.yourdomain.com

# === DATABASE ===
DATABASE_URL=postgresql://user:password@host:5432/dbname
# OR for SQLite (not recommended for production)
# DATABASE_URL=sqlite:///db.sqlite3

# === SHOPIFY API ===
SHOPIFY_STORE_URL=7fa66c-ac.myshopify.com
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_ACCESS_TOKEN=your_access_token
SHOPIFY_API_VERSION=2025-01

# === CORS (Frontend URLs) ===
FRONTEND_URL=https://yourdomain.com
SHOPIFY_ADMIN_URL=https://7fa66c-ac.myshopify.com

# === EMAIL (Optional) ===
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# === REDIS (Optional - for caching) ===
REDIS_URL=redis://localhost:6379/0

# === SENTRY (Optional - for error tracking) ===
SENTRY_DSN=your-sentry-dsn
```

**Action Required:**
- [ ] Create this file with your actual values
- [ ] Provide missing values (I'll help get them)
- [ ] Never commit this file to git (already in .gitignore)

---

## 🎯 PART 2: PRE-DEPLOYMENT CHECKLIST

### A. Verify Current System Status

Run these checks on your local system:

#### 1. Django Backend Health Check

```bash
# Navigate to backend
cd app/lavish_backend

# Check if server runs
python manage.py runserver 8003

# In another terminal, test API
curl http://127.0.0.1:8003/api/subscriptions/selling-plans/?product_id=123
```

**Expected:** HTTP 200 or 404 (not 500)

**Action Required:**
- [ ] Confirm Django runs without errors
- [ ] Fix any startup errors before proceeding

#### 2. Database Migrations Status

```bash
cd app/lavish_backend

# Check for pending migrations
python manage.py showmigrations

# Apply any pending migrations
python manage.py migrate
```

**Action Required:**
- [ ] All migrations must be applied
- [ ] No red `[ ]` should show (all should be `[X]`)

#### 3. Static Files Collection

```bash
cd app/lavish_backend

# Collect static files for production
python manage.py collectstatic --noinput
```

**Action Required:**
- [ ] Confirm completes without errors
- [ ] Creates/updates `staticfiles/` directory

#### 4. Theme Syntax Validation

```bash
cd app/crave_theme  # or lavish_frontend

# Validate theme structure
shopify theme check
```

**Action Required:**
- [ ] Fix any critical errors
- [ ] Warnings are okay but note them

---

### B. Data Validation

#### 1. Check Products Have Selling Plans

```bash
cd app/lavish_backend

# Open Django shell
python manage.py shell

# Run these commands:
from products.models import ShopifyProduct
from customer_subscriptions.models import SellingPlan

print(f"Products: {ShopifyProduct.objects.count()}")
print(f"Selling Plans: {SellingPlan.objects.filter(is_active=True).count()}")
print(f"Plans synced to Shopify: {SellingPlan.objects.filter(shopify_id__isnull=False).count()}")
```

**Expected Output:**
```
Products: 10 (or your product count)
Selling Plans: 3 (or your plan count)
Plans synced to Shopify: 3 (should match plan count)
```

**Action Required:**
- [ ] If "Plans synced" is 0, selling plans need to be pushed to Shopify
- [ ] I'll provide commands to sync them

#### 2. Verify Database Connections

```bash
cd app/lavish_backend

# Test database connection
python manage.py dbshell
# Type: \q (to quit)
```

**Action Required:**
- [ ] Confirm database connects successfully
- [ ] Fix connection issues before proceeding

---

## 🎯 PART 3: STEP-BY-STEP DEPLOYMENT

### Phase 1: Prepare Backend for Production

#### Step 1.1: Update Django Settings for Production

**File:** `app/lavish_backend/core/settings.py`

Changes needed:

```python
# Line 32: Set DEBUG to False for production
DEBUG = False  # Change from True

# Lines 34-41: Add your production domains
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'lavish-backend.endevops.net',  # Your current backend
    'api.yourdomain.com',  # If you have custom domain
    '.myshopify.com',  # Keep for Shopify
]

# Lines 44-49: Add production URLs to CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://lavish-backend.endevops.net',
    'https://api.yourdomain.com',
    'https://yourdomain.com',  # Your store
    'https://7fa66c-ac.myshopify.com',  # Shopify admin
]

# Lines 474-493: Update CORS for production
CORS_ALLOWED_ORIGINS = [
    'https://lavish-backend.endevops.net',
    'https://7fa66c-ac.myshopify.com',
    'https://yourdomain.com',  # Your custom domain
    # Remove all localhost/127.0.0.1 entries for production
]

# Line 496: Disable promiscuous CORS
CORS_ALLOW_ALL_ORIGINS = False  # Change from True
```

**Action Required:**
- [ ] Make these changes
- [ ] Replace `yourdomain.com` with your actual domain
- [ ] Test locally after changes

#### Step 1.2: Create Production Requirements File

**File:** `app/lavish_backend/requirements-production.txt`

```txt
# Copy from requirements.txt and add:
gunicorn==21.2.0
psycopg2-binary==2.9.9
whitenoise==6.6.0
sentry-sdk==1.39.1
redis==5.0.1
```

**Action Required:**
- [ ] Create this file
- [ ] Install on production server

#### Step 1.3: Create Deployment Scripts

**File:** `app/lavish_backend/deploy.sh`

```bash
#!/bin/bash
# Deployment script for Lavish Library Backend

echo "=== Starting Deployment ==="

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements-production.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "=== Deployment Complete ==="
```

**Action Required:**
- [ ] Create this file
- [ ] Make executable: `chmod +x deploy.sh`
- [ ] Customize for your server setup

---

### Phase 2: Deploy Django Backend

#### Option A: Deploy to Existing Server (lavish-backend.endevops.net)

**Step 2.1: Connect to Server**

```bash
ssh username@lavish-backend.endevops.net
# Enter password when prompted
```

**Action Required:**
- [ ] Provide SSH credentials
- [ ] Or provide alternative access method (FTP, cPanel, etc.)

**Step 2.2: Update Code on Server**

```bash
# Navigate to project directory
cd /path/to/lavish  # You need to provide this path

# Backup current version
cp -r app/lavish_backend app/lavish_backend.backup.$(date +%Y%m%d)

# Pull latest changes
git pull origin main

# OR upload via FTP/SCP if not using git
```

**Action Required:**
- [ ] Provide project path on server
- [ ] Choose update method (git/FTP/other)

**Step 2.3: Install Dependencies**

```bash
cd app/lavish_backend

# Activate virtual environment (if exists)
source venv/bin/activate  # or: . venv/bin/activate

# Install/update packages
pip install -r requirements.txt
```

**Action Required:**
- [ ] Confirm virtual environment path
- [ ] Or I'll help create one

**Step 2.4: Run Migrations**

```bash
python manage.py migrate
```

**Expected:** All migrations apply successfully

**Step 2.5: Collect Static Files**

```bash
python manage.py collectstatic --noinput
```

**Step 2.6: Restart Server**

```bash
# For Gunicorn + Systemd
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# For Apache
sudo systemctl restart apache2

# For cPanel/Passenger
# Touch restart file (path varies)
touch tmp/restart.txt
```

**Action Required:**
- [ ] Provide your server type
- [ ] I'll give specific restart commands

**Step 2.7: Verify Deployment**

```bash
# Test API endpoint
curl https://lavish-backend.endevops.net/api/subscriptions/selling-plans/?product_id=123

# Check logs
tail -f /var/log/gunicorn/access.log  # Path may vary
```

**Expected:** API responds (200 or 404, not 500)

---

#### Option B: Deploy to New Server

If you need a new server, I'll provide full setup guide including:
- Server provisioning
- Nginx/Gunicorn configuration
- SSL certificate setup
- Database setup
- Environment configuration

**Action Required:**
- [ ] Choose hosting provider
- [ ] I'll provide complete setup instructions

---

### Phase 3: Deploy Shopify Theme

#### Step 3.1: Prepare Theme for Production

**Update API URLs in Theme**

**File:** `app/crave_theme/snippets/product-subscription-options.liquid`

Find and update (around lines 468-470):

```javascript
// BEFORE (Development URLs):
var checkoutEndpoints = [
  'http://127.0.0.1:8003/api/subscriptions/checkout/create/',
  'http://localhost:8003/api/subscriptions/checkout/create/',
  '/api/subscriptions/checkout/create/'
];

// AFTER (Production URLs):
var checkoutEndpoints = [
  'https://lavish-backend.endevops.net/api/subscriptions/checkout/create/',
  '/api/subscriptions/checkout/create/'  // Fallback
];
```

Similarly update around line 328:

```javascript
// BEFORE:
const apiEndpoints = [
  'http://127.0.0.1:8003/api/subscriptions/selling-plans/?product_id=' + productId,
  'http://localhost:8003/api/subscriptions/selling-plans/?product_id=' + productId,
  '/api/subscriptions/selling-plans/?product_id=' + productId
];

// AFTER:
const apiEndpoints = [
  'https://lavish-backend.endevops.net/api/subscriptions/selling-plans/?product_id=' + productId,
  '/api/subscriptions/selling-plans/?product_id=' + productId  // Fallback
];
```

**Action Required:**
- [ ] Make these changes
- [ ] Commit to git

#### Step 3.2: Install Shopify CLI

```bash
# Windows (PowerShell as Administrator)
npm install -g @shopify/cli@latest

# Verify installation
shopify version
```

**Action Required:**
- [ ] Install Shopify CLI
- [ ] Confirm version shows (e.g., "3.x.x")

#### Step 3.3: Authenticate with Shopify

```bash
cd app/crave_theme

# Login to Shopify
shopify auth login
```

This will:
1. Open browser window
2. Ask you to log in to Shopify admin
3. Grant permissions
4. Return to terminal

**Action Required:**
- [ ] Complete authentication
- [ ] Confirm "Logged in to [your-store]" message

#### Step 3.4: Push Theme to Shopify

**Option A: Push as Unpublished (Recommended for first deploy)**

```bash
shopify theme push --unpublished --theme="Lavish Custom Theme"
```

This creates a new theme you can preview before publishing.

**Option B: Push to Existing Theme**

```bash
# List existing themes
shopify theme list

# Push to specific theme
shopify theme push --theme=<THEME_ID>
```

**Option C: Push and Publish Immediately**

```bash
shopify theme push --publish
```

**Action Required:**
- [ ] Choose deployment method
- [ ] Confirm theme uploads successfully
- [ ] Note theme ID for future updates

#### Step 3.5: Preview and Test

```bash
# Get preview URL
shopify theme share

# Or open in browser
shopify theme open
```

**Testing Checklist:**
- [ ] Homepage loads correctly
- [ ] Product pages show subscription options
- [ ] Subscribe button works
- [ ] Cart adds subscription items
- [ ] Checkout completes successfully
- [ ] Customer account page works
- [ ] API calls succeed (check browser console)

---

### Phase 4: Configure Webhooks

Shopify needs to notify Django when subscriptions are created/updated.

#### Step 4.1: Get Webhook URLs

Your webhook endpoints (already exist in Django):
```
https://lavish-backend.endevops.net/api/subscriptions/webhooks/subscription-contracts/create/
https://lavish-backend.endevops.net/api/subscriptions/webhooks/subscription-contracts/update/
https://lavish-backend.endevops.net/api/subscriptions/webhooks/subscription-billing-attempts/success/
https://lavish-backend.endevops.net/api/subscriptions/webhooks/subscription-billing-attempts/failure/
```

#### Step 4.2: Register Webhooks in Shopify

**Method A: Via Shopify Admin (Manual)**

1. Go to: `Settings → Notifications → Webhooks`
2. Click "Create webhook"
3. For each webhook:
   - Event: Select event type (e.g., "Subscription contracts create")
   - Format: JSON
   - URL: Enter webhook URL from above
   - API version: 2025-01

**Method B: Via Django Management Command**

```bash
cd app/lavish_backend

# Register all webhooks automatically
python manage.py register_webhooks
```

**Action Required:**
- [ ] Choose method
- [ ] Register all 4 webhooks
- [ ] Test webhook delivery

#### Step 4.3: Verify Webhook Setup

```bash
# Check webhook logs
cd app/lavish_backend
tail -f logs/django.log | grep webhook
```

---

### Phase 5: Sync Data to Production

#### Step 5.1: Sync Products from Shopify

```bash
cd app/lavish_backend

# Sync all products
python manage.py sync_products

# Verify
python manage.py shell
>>> from products.models import ShopifyProduct
>>> print(ShopifyProduct.objects.count())
```

**Action Required:**
- [ ] Confirm products sync successfully
- [ ] Fix any sync errors

#### Step 5.2: Push Selling Plans to Shopify

```bash
# Check current selling plans
python manage.py shell
>>> from customer_subscriptions.models import SellingPlan
>>> for plan in SellingPlan.objects.filter(is_active=True):
...     print(f"{plan.name}: shopify_id={plan.shopify_id}")

# If shopify_id is None, push to Shopify:
# Via Django Admin:
# 1. Go to http://lavish-backend.endevops.net/admin/
# 2. Navigate to Selling Plans
# 3. Select plans
# 4. Action: "Push to Shopify"
# 5. Click "Go"
```

**Action Required:**
- [ ] Ensure all selling plans have shopify_id
- [ ] Test subscription purchase works

#### Step 5.3: Associate Products with Selling Plans

```bash
# Via Django Admin:
# 1. Go to Selling Plans
# 2. Edit each plan
# 3. Select products in "Products" field
# 4. Save
# 5. Click "Sync product associations to Shopify"
```

**Action Required:**
- [ ] Associate products with appropriate plans
- [ ] Verify on Shopify product pages

---

## 🎯 PART 4: PRODUCTION CONFIGURATION

### A. Security Hardening

#### 1. Update Django Security Settings

**File:** `app/lavish_backend/core/settings.py`

Add these security settings:

```python
# After DEBUG = False

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Admin security
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')  # Change from 'admin/'
```

**Action Required:**
- [ ] Add these settings
- [ ] Set ADMIN_URL in .env to something secret (e.g., 'secure-admin-panel-2024/')

#### 2. Configure Firewall

```bash
# On server
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

#### 3. Set Up Backups

**Database Backup Script:**

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/lavish"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump dbname > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /path/to/media

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

**Action Required:**
- [ ] Create backup script
- [ ] Set up cron job: `0 2 * * * /path/to/backup.sh`

---

### B. Monitoring & Logging

#### 1. Set Up Error Tracking (Sentry)

```bash
pip install sentry-sdk
```

**File:** `app/lavish_backend/core/settings.py`

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
    environment='production'
)
```

**Action Required:**
- [ ] Create free Sentry account
- [ ] Get DSN
- [ ] Add to .env

#### 2. Configure Application Logging

**File:** `app/lavish_backend/core/settings.py`

Update LOGGING configuration:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'customer_subscriptions': {
            'handlers': ['file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**Action Required:**
- [ ] Create logs directory: `mkdir app/lavish_backend/logs`
- [ ] Set proper permissions: `chmod 755 logs`

---

## 🎯 PART 5: POST-DEPLOYMENT VERIFICATION

### A. Functionality Testing

#### 1. Test Subscription Purchase Flow

**Test Steps:**
1. [ ] Go to product page
2. [ ] Verify subscription options display
3. [ ] Click "Subscribe" button
4. [ ] Verify item added to cart with subscription
5. [ ] Proceed to checkout
6. [ ] Complete test purchase
7. [ ] Verify subscription created in:
   - [ ] Shopify Admin → Apps → Subscriptions
   - [ ] Django Admin → Customer Subscriptions

#### 2. Test Customer Account

**Test Steps:**
1. [ ] Log in to customer account
2. [ ] Navigate to account page
3. [ ] Verify custom dashboard loads
4. [ ] Check "Subscriptions" tab
5. [ ] Test subscription management features
6. [ ] Verify API calls succeed (check console)

#### 3. Test Admin Functions

**Django Admin:**
1. [ ] Access: `https://lavish-backend.endevops.net/secure-admin-panel-2024/`
2. [ ] Test login
3. [ ] View customer subscriptions
4. [ ] View orders
5. [ ] Test selling plan management

**Shopify Admin:**
1. [ ] Check subscriptions section
2. [ ] Verify webhook logs
3. [ ] Check theme customization

---

### B. Performance Testing

#### 1. API Response Times

```bash
# Test API endpoints
curl -w "@curl-format.txt" -o /dev/null -s \
  "https://lavish-backend.endevops.net/api/subscriptions/selling-plans/?product_id=123"

# Create curl-format.txt:
time_total: %{time_total}s
```

**Expected:** < 500ms

#### 2. Page Load Times

Use browser DevTools:
- Network tab
- Performance tab
- Check Core Web Vitals

**Targets:**
- LCP (Largest Contentful Paint): < 2.5s
- FID (First Input Delay): < 100ms
- CLS (Cumulative Layout Shift): < 0.1

---

## 🎯 PART 6: TROUBLESHOOTING GUIDE

### Common Issues and Solutions

#### Issue 1: API Calls Failing (CORS Errors)

**Symptoms:**
- Browser console shows CORS errors
- Subscription options don't load

**Solution:**
```python
# In settings.py, ensure:
CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
    'https://7fa66c-ac.myshopify.com',
]
CORS_ALLOW_CREDENTIALS = True
```

#### Issue 2: Checkout Redirect Fails

**Symptoms:**
- Subscribe button doesn't work
- No redirect to checkout

**Solution:**
- Verify production URL in theme files
- Check browser console for errors
- Verify environment detection (should be production, not local)

#### Issue 3: Webhooks Not Received

**Symptoms:**
- Subscriptions created in Shopify
- Not showing in Django admin

**Solution:**
```bash
# Check webhook registration
curl https://lavish-backend.endevops.net/api/subscriptions/webhooks/test

# Check logs
tail -f logs/django.log | grep webhook

# Re-register webhooks
python manage.py register_webhooks
```

#### Issue 4: Static Files Not Loading

**Symptoms:**
- CSS/JS not working
- Images missing

**Solution:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Nginx/Apache configuration
# Ensure static files served correctly
```

---

## 🎯 PART 7: MAINTENANCE & UPDATES

### A. Regular Maintenance Tasks

#### Daily
- [ ] Monitor error logs
- [ ] Check webhook delivery
- [ ] Review failed subscriptions

#### Weekly
- [ ] Database backup verification
- [ ] Security updates check
- [ ] Performance monitoring

#### Monthly
- [ ] Full system backup
- [ ] Dependency updates
- [ ] Security audit

### B. Update Procedures

#### Updating Django Backend

```bash
# 1. Backup first
./backup.sh

# 2. Pull updates
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Collect static
python manage.py collectstatic --noinput

# 6. Restart
sudo systemctl restart gunicorn
```

#### Updating Shopify Theme

```bash
cd app/crave_theme

# Pull from git
git pull origin main

# Push to Shopify
shopify theme push --theme=<THEME_ID>
```

---

## 🎯 PART 8: SUCCESS METRICS

### What to Monitor

#### Business Metrics
- Subscription conversion rate
- Average order value
- Customer lifetime value
- Churn rate

#### Technical Metrics
- API response time
- Error rate
- Uptime percentage
- Page load time

#### Customer Experience
- Checkout completion rate
- Support ticket volume
- Customer satisfaction score

---

## 📋 FINAL CHECKLIST

### Pre-Go-Live
- [ ] All environment variables configured
- [ ] Database backed up
- [ ] Theme deployed to Shopify
- [ ] Backend deployed and running
- [ ] Webhooks configured and tested
- [ ] SSL certificates valid
- [ ] DNS configured correctly
- [ ] Monitoring tools set up
- [ ] Backup system operational
- [ ] Test purchases completed successfully

### Go-Live Day
- [ ] Switch Shopify theme to new version
- [ ] Monitor error logs closely
- [ ] Test all critical flows
- [ ] Have rollback plan ready
- [ ] Monitor customer feedback
- [ ] Track sales/conversions

### Post-Launch (First Week)
- [ ] Daily monitoring
- [ ] Address any issues immediately
- [ ] Collect customer feedback
- [ ] Fine-tune performance
- [ ] Document any issues/solutions

---

## 🆘 EMERGENCY CONTACTS & ROLLBACK

### Rollback Procedures

#### If Theme Has Issues:
```bash
# Via Shopify Admin
1. Go to: Online Store → Themes
2. Find previous theme
3. Click "Actions" → "Publish"
```

#### If Backend Has Issues:
```bash
# On server
cd /path/to/lavish
git reset --hard <previous-commit-hash>
sudo systemctl restart gunicorn
```

### Emergency Commands

```bash
# Quick health check
curl https://lavish-backend.endevops.net/admin/
curl https://yourdomain.com

# View recent errors
tail -100 logs/errors.log

# Database restore
psql dbname < backup.sql
```

---

## 📞 NEXT STEPS - WHAT I NEED FROM YOU

To proceed with deployment, please provide:

### Priority 1 (Required Now):
1. **Confirm backend server access**
   - [ ] Server URL: `lavish-backend.endevops.net`
   - [ ] Access method: SSH / FTP / Other?
   - [ ] Login credentials (via secure method)

2. **Confirm .env values**
   - [ ] Do you have a .env file?
   - [ ] Are Shopify credentials populated?
   - [ ] Share (securely) if missing values

3. **Choose theme to deploy**
   - [ ] `crave_theme` (has checkout fixes) ✅ Recommended
   - [ ] `lavish_frontend` (has enhanced account)
   - [ ] Merge both?

### Priority 2 (Needed Soon):
4. **Custom domain info**
   - [ ] Do you have a custom domain?
   - [ ] If yes, what is it?
   - [ ] DNS access available?

5. **Production deployment method**
   - [ ] Deploy to existing server (lavish-backend.endevops.net)
   - [ ] Set up new server
   - [ ] Use managed hosting (Heroku/PythonAnywhere/etc.)

### Priority 3 (Optional but Recommended):
6. **Monitoring setup**
   - [ ] Create Sentry account for error tracking
   - [ ] Set up uptime monitoring
   - [ ] Configure email alerts

---

## 📝 CONCLUSION

This guide provides everything needed for a successful hybrid deployment. The system will:

✅ Use Shopify for payments (PCI compliant, secure)
✅ Use Django for custom business logic
✅ Provide custom customer experience
✅ Support advanced subscription management
✅ Maintain all existing functionality
✅ Be scalable for future growth

**Once you provide the information in "NEXT STEPS", I'll:**
1. Create specific deployment commands for your setup
2. Guide you through each step
3. Help troubleshoot any issues
4. Verify everything works correctly

**Estimated deployment time:** 2-4 hours (depending on server setup)

---

*Guide Created: December 13, 2025*  
*For: Lavish Library Production Deployment*  
*Architecture: Hybrid Shopify + Django System*

