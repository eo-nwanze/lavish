# Lavish Library - Production Architecture

## 🏗️ SYSTEM ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                         CUSTOMER BROWSER                         │
│                  (https://lavishlibrary.com.au)                  │
└────────────┬─────────────────────────────────────────┬──────────┘
             │                                          │
             │                                          │
             v                                          v
┌────────────────────────────┐              ┌──────────────────────┐
│   SHOPIFY INFRASTRUCTURE   │              │   DJANGO BACKEND     │
│  (Shopify Hosted/Managed)  │              │  (Your Server/Cloud) │
├────────────────────────────┤              ├──────────────────────┤
│                            │              │                      │
│  ┌──────────────────────┐  │              │  ┌────────────────┐ │
│  │  Liquid Theme        │  │              │  │  REST API      │ │
│  │  (Your Custom Theme) │  │◄─────────────┼──│  Endpoints     │ │
│  │                      │  │   CORS       │  │                │ │
│  │  • enhanced-account  │  │   Enabled    │  │  • /locations/ │ │
│  │  • main-product      │  │              │  │  • /customers/ │ │
│  │  • subscriptions     │  │              │  │  • /orders/    │ │
│  │  • django-integration│  │              │  │  • /api/       │ │
│  └──────────────────────┘  │              │  └────────────────┘ │
│             │               │              │          │          │
│             v               │              │          v          │
│  ┌──────────────────────┐  │              │  ┌────────────────┐ │
│  │  Shopify Checkout    │  │              │  │  PostgreSQL    │ │
│  │  (Subscriptions)     │  │              │  │  Database      │ │
│  └──────────────────────┘  │              │  └────────────────┘ │
│             │               │              │          │          │
│             v               │              │          v          │
│  ┌──────────────────────┐  │              │  ┌────────────────┐ │
│  │  Shopify Admin API   │◄─┼──────────────┼──│  Sync Service  │ │
│  │  (GraphQL/REST)      │  │  Webhooks    │  │  (Bidirectional│ │
│  │                      │  │              │  │   Sync)        │ │
│  │  • Products          │  │              │  └────────────────┘ │
│  │  • Orders            │  │              │          │          │
│  │  • Customers         │  │              │          v          │
│  │  • Subscriptions     │  │              │  ┌────────────────┐ │
│  │  • Selling Plans     │  │              │  │  Redis Cache   │ │
│  └──────────────────────┘  │              │  └────────────────┘ │
│             │               │              │                      │
│             v               │              └──────────────────────┘
│  ┌──────────────────────┐  │                         │
│  │  Shopify Payments    │  │                         │
│  │  (PCI Compliant)     │  │                         │
│  └──────────────────────┘  │                         │
│                            │                         │
└────────────────────────────┘                         │
             │                                          │
             v                                          v
┌────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                │
├────────────────────────────────────────────────────────────────┤
│  1. Customer visits site → Sees Custom Liquid Theme             │
│  2. Theme makes API calls → Django Backend for enhanced features│
│  3. Customer adds to cart → Shopify handles cart/checkout       │
│  4. Order placed → Shopify processes payment                    │
│  5. Webhooks fire → Django syncs data                           │
│  6. Customer logs in → Enhanced account page loads              │
│  7. Account page calls → Django API for dynamic data            │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔄 DATA SYNCHRONIZATION FLOW

```
┌───────────────┐                                    ┌───────────────┐
│    SHOPIFY    │                                    │    DJANGO     │
│               │                                    │               │
│  Products     │────────Webhooks (Create/Update)──►│  Products     │
│  Orders       │────────Webhooks (Create/Update)──►│  Orders       │
│  Customers    │────────Webhooks (Create/Update)──►│  Customers    │
│  Subscriptions│────────Webhooks (Create/Update)──►│  Subscriptions│
│               │                                    │               │
│  Selling Plans│◄────GraphQL Mutations (Create)────│  Selling Plans│
│  Products     │◄────GraphQL Mutations (Associate)─│  Products     │
│               │                                    │               │
└───────────────┘                                    └───────────────┘
       ▲                                                      │
       │                                                      │
       └──────────────── Bidirectional Sync ─────────────────┘
```

---

## 🌐 REQUEST FLOW EXAMPLES

### **Example 1: Customer Visits Product Page**

```
Customer Browser
    │
    ├─→ GET https://lavishlibrary.com.au/products/book-title
    │
    v
Shopify CDN (Fast Global Delivery)
    │
    ├─→ Loads: main-product.liquid template
    │   Includes: subscription-purchase-options.liquid
    │
    v
Browser renders page with:
    ├─ Product info (from Shopify)
    ├─ Images (from Shopify CDN)
    └─ Subscription options (from product.selling_plan_groups)
```

### **Example 2: Customer Manages Account**

```
Customer Browser
    │
    ├─→ GET https://lavishlibrary.com.au/account
    │
    v
Shopify serves enhanced-account.liquid
    │
    ├─→ Page loads with customer data (from Shopify)
    │
    v
JavaScript (django-integration.js) executes
    │
    ├─→ GET https://api.lavishlibrary.com.au/api/locations/countries/
    ├─→ GET https://api.lavishlibrary.com.au/api/customers/{id}/
    │
    v
Django API responds with:
    ├─ 8 countries with states/cities
    ├─ Enhanced customer data
    └─ Additional features
    │
    v
Page dynamically updates with:
    ├─ Populated address forms
    ├─ Real-time order status
    └─ Subscription management
```

### **Example 3: Customer Creates Subscription Order**

```
1. Customer selects subscription option
    │
    v
2. JavaScript updates hidden input:
   <input name="selling_plan" value="6324125790">
    │
    v
3. Add to cart (Shopify Ajax API)
   POST /cart/add.js
   Body: {
     id: variant_id,
     quantity: 1,
     selling_plan: 6324125790
   }
    │
    v
4. Shopify Checkout
   → Customer completes payment
   → Subscription contract created
    │
    v
5. Shopify fires webhook
   → POST https://api.lavishlibrary.com.au/webhooks/subscription-created/
    │
    v
6. Django processes webhook
   → Creates CustomerSubscription record
   → Syncs data
   → Triggers email notification
```

---

## 🔐 SECURITY ARCHITECTURE

```
┌────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: HTTPS/SSL (Shopify + Your Backend)              │
│  ├─ Shopify: Automatic SSL for custom domains              │
│  └─ Backend: Let's Encrypt or CloudFlare SSL               │
│                                                             │
│  Layer 2: CORS Protection                                  │
│  ├─ Only allow requests from your Shopify domain           │
│  └─ Configured in Django settings                          │
│                                                             │
│  Layer 3: Authentication                                   │
│  ├─ Shopify customer authentication (session-based)        │
│  ├─ Django API requires customer verification              │
│  └─ Webhook signature verification (HMAC)                  │
│                                                             │
│  Layer 4: Authorization                                    │
│  ├─ Customers can only access their own data               │
│  ├─ Admin endpoints protected by Django permissions        │
│  └─ Rate limiting on API endpoints                         │
│                                                             │
│  Layer 5: Data Protection                                  │
│  ├─ PCI compliance via Shopify Payments                    │
│  ├─ Encrypted database connections                         │
│  ├─ Sensitive data encrypted at rest                       │
│  └─ Regular security audits                                │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 💾 DATABASE SCHEMA (Django)

```
┌─────────────────┐      ┌──────────────────┐
│ ShopifyCustomer │──────│ CustomerAddress  │
│                 │ 1:N  │                  │
│ • shopify_id    │      │ • customer_id    │
│ • email         │      │ • address1       │
│ • first_name    │      │ • city           │
│ • last_name     │      │ • country        │
└────────┬────────┘      └──────────────────┘
         │
         │ 1:N
         │
┌────────▼────────────┐
│ CustomerSubscription│
│                     │
│ • customer_id       │──┐
│ • selling_plan_id   │  │
│ • shopify_id        │  │ N:1
│ • status            │  │
│ • next_billing_date │  │
└─────────────────────┘  │
                         │
         ┌───────────────┘
         │
┌────────▼────────┐      ┌──────────────────┐
│ SellingPlan     │──────│ ShopifyProduct   │
│                 │ M:N  │                  │
│ • shopify_id    │      │ • shopify_id     │
│ • name          │      │ • title          │
│ • billing_policy│      │ • price          │
│ • price_adj     │      │ • variants       │
└─────────────────┘      └──────────────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│ ShopifyOrder    │
│                 │
│ • shopify_id    │
│ • customer_id   │
│ • order_number  │
│ • total_price   │
│ • status        │
└─────────────────┘
```

---

## 📈 SCALABILITY PLAN

### **Phase 1: Launch (0-1k orders/month)**
```
├─ Shopify Basic Plan
├─ Single DigitalOcean Droplet ($12/mo)
├─ PostgreSQL on same server
└─ Cost: ~$50/month
```

### **Phase 2: Growth (1k-10k orders/month)**
```
├─ Shopify Standard Plan
├─ Load balanced application servers (2x)
├─ Managed PostgreSQL (RDS/DO)
├─ Redis cache layer
└─ Cost: ~$200/month
```

### **Phase 3: Scale (10k+ orders/month)**
```
├─ Shopify Advanced/Plus Plan
├─ Kubernetes cluster (auto-scaling)
├─ CDN for API responses
├─ Read replicas for database
├─ Dedicated monitoring/logging
└─ Cost: ~$1000+/month
```

---

## 🎯 DEPLOYMENT STRATEGY

### **Development**
```
Local Machine
├─ Django: localhost:8000
├─ Shopify CLI: localhost:9292
└─ Git: feature branches
```

### **Staging**
```
Staging Environment
├─ Django: staging-api.lavishlibrary.com.au
├─ Shopify: Unpublished theme for testing
└─ Git: staging branch
```

### **Production**
```
Production Environment
├─ Django: api.lavishlibrary.com.au
├─ Shopify: Published theme (live)
└─ Git: main branch (protected)
```

### **Deployment Pipeline**
```
Developer
    │
    ├─→ Push to feature branch
    │
    v
GitHub Actions (CI/CD)
    │
    ├─→ Run tests
    ├─→ Lint code
    │
    v
Merge to staging
    │
    ├─→ Auto-deploy to staging
    ├─→ Run integration tests
    │
    v
Manual approval
    │
    v
Merge to main
    │
    ├─→ Deploy to production
    ├─→ Health checks
    ├─→ Rollback if needed
    │
    v
Production Live ✅
```

---

## 📊 MONITORING DASHBOARD

### **Key Metrics to Track**

```
┌─────────────────────────────────────────┐
│         SYSTEM HEALTH DASHBOARD          │
├─────────────────────────────────────────┤
│                                          │
│  API Response Time                       │
│  ████████░░ 85ms avg (target: <100ms)   │
│                                          │
│  Error Rate                              │
│  ██░░░░░░░░ 0.2% (target: <1%)          │
│                                          │
│  Webhook Success Rate                    │
│  ██████████ 99.8% (target: >99%)        │
│                                          │
│  Database Query Time                     │
│  ██████░░░░ 45ms avg (target: <50ms)    │
│                                          │
│  Orders Synced (24h)                     │
│  ██████████ 156 orders                   │
│                                          │
│  Active Subscriptions                    │
│  ██████████ 423 subscriptions            │
│                                          │
└─────────────────────────────────────────┘
```

---

## ✅ YOUR RECOMMENDED PATH

**For Lavish Library, deploy as:**

1. **Shopify Theme** (Your custom Liquid frontend)
   - Fast deployment
   - Leverages Shopify infrastructure
   - Professional checkout experience

2. **Django Backend** (Enhanced features API)
   - Heroku or DigitalOcean
   - PostgreSQL database
   - Redis caching

3. **Custom Domain**
   - lavishlibrary.com.au → Shopify store
   - api.lavishlibrary.com.au → Django backend

**Timeline: 4 hours + DNS propagation**
**Cost: ~$50-100/month**
**Maintenance: Low**

---

See `DEPLOYMENT_GUIDE_COMPLETE.md` for step-by-step instructions!

