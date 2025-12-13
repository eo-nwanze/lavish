# Quick Deployment Reference - TL;DR

## 🚀 FASTEST PATH TO PRODUCTION

### **Step 1: Deploy Django Backend** (30 minutes)

**Option A: Heroku (Easiest)**
```bash
cd app/lavish_backend
heroku create lavish-api
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku run python manage.py migrate
```

**Option B: DigitalOcean** ($12/month)
- Create droplet with Ubuntu
- Install: Python, Nginx, PostgreSQL, Redis
- Deploy with Gunicorn + Nginx + SSL

### **Step 2: Update Frontend API URLs** (5 minutes)

Edit `app/lavish_frontend/assets/django-integration.js`:
```javascript
// Line 1-2, change:
const API_BASE_URL = 'https://your-backend.herokuapp.com';
```

### **Step 3: Deploy Shopify Theme** (15 minutes)

```bash
cd app/lavish_frontend

# Install Shopify CLI
npm install -g @shopify/cli@latest

# Login
shopify auth login

# Push theme
shopify theme push --unpublished  # Test first
shopify theme push --publish      # When ready
```

### **Step 4: Configure Domain** (24-48 hours for DNS)

1. Add A records to your domain DNS:
   ```
   A    @      23.227.38.65
   A    www    23.227.38.65
   CNAME api   your-backend.com
   ```

2. In Shopify Admin → Domains → "Connect existing domain"

3. Wait for SSL provisioning

### **Step 5: Remove Store Password** (1 minute)

Shopify Admin → Online Store → Preferences → Remove password

## ✅ DONE!

Your custom frontend is now live at:
- **Main Store:** https://lavishlibrary.com.au
- **API Backend:** https://api.lavishlibrary.com.au

---

## 🔧 PRODUCTION CHECKLIST

```
Backend:
☐ Environment variables set
☐ CORS allowed origins updated
☐ Database migrated
☐ Webhooks registered
☐ SSL enabled

Frontend:
☐ API URLs point to production
☐ Theme validated (no errors)
☐ Mobile tested
☐ Products published
☐ Selling plans active

Shopify:
☐ Payment gateway configured
☐ Shipping set up
☐ Custom domain connected
☐ Store password removed
```

---

## 📊 ESTIMATED TIMELINE

| Task | Time |
|------|------|
| Backend deployment | 30-60 min |
| Frontend updates | 15 min |
| Theme upload | 15 min |
| Domain configuration | 5 min (+ 24-48hr DNS) |
| Testing | 2-4 hours |
| **TOTAL** | **~4 hours + DNS wait** |

---

## 💰 MONTHLY COSTS

**Minimal Setup:** ~$52/month
- Shopify Basic: $39
- Backend (DO/Heroku): $12-15

**Standard Setup:** ~$163/month
- Shopify Plan: $105
- Better backend: $35-50
- Database: $20

---

## 🆘 COMMON ISSUES

**Issue:** API not accessible from Shopify
- **Fix:** Check CORS settings in Django

**Issue:** Theme errors after upload
- **Fix:** Validate with `shopify theme check`

**Issue:** Subscriptions not showing
- **Fix:** Run `python manage.py sync_selling_plan_products`

**Issue:** Domain not connecting
- **Fix:** Verify DNS records, wait 24-48 hours

---

## 📞 NEED HELP?

- Shopify Support: https://help.shopify.com
- Django Docs: https://docs.djangoproject.com
- Deployment Issues: Check server logs

**Your complete guide:** See `DEPLOYMENT_GUIDE_COMPLETE.md`

