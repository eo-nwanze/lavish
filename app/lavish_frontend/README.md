# 🎨 **Crave Theme with Django Integration**

A premium Shopify theme enhanced with Django backend integration for advanced customer analytics and personalization.

---

## 🚀 **Quick Start**

### **1. Start Development Server**
```bash
# Double-click or run:
start-theme-dev.bat

# Or manually:
shopify theme dev --store 7fa66c-ac.myshopify.com
```

### **2. Access URLs**
- **Theme Preview**: http://127.0.0.1:9292
- **Django Backend**: http://127.0.0.1:8000/admin/
- **Shopify Store**: https://7fa66c-ac.myshopify.com

---

## 🏗️ **Architecture**

### **Theme Structure**
```
lavish_frontend/
├── assets/              # CSS, JS, images, fonts
│   ├── django-integration.js    # Django backend communication
│   ├── base.css                 # Core Crave theme styles
│   └── component-*.css          # Component-specific styles
├── config/              # Theme settings and markets
├── layout/              # Page layouts with Django integration
├── locales/             # Multi-language support (25+ languages)
├── sections/            # Modular page sections
│   ├── django-products.liquid  # Custom Django-powered section
│   └── *.liquid                # Crave theme sections
├── snippets/            # Reusable code fragments
└── templates/           # Page templates (JSON-based)
```

### **Integration Features**
- ✅ **Customer Tracking** - Automatic sync with Django backend
- ✅ **Real-time Analytics** - Page views, cart events, form submissions
- ✅ **Personalization** - Customer-specific content and recommendations
- ✅ **Inventory Sync** - Live stock levels from Django database
- ✅ **Custom Sections** - Django-powered product displays

---

## 🎯 **Key Features**

### **Crave Theme Features**
- **Premium Design** - Modern, professional e-commerce layout
- **Responsive** - Mobile-first design with tablet/desktop optimization
- **Customizable** - 100+ theme settings via Shopify admin
- **Performance** - Optimized for speed and SEO
- **Accessibility** - WCAG compliant with screen reader support
- **Multi-language** - Support for 25+ languages and locales

### **Django Integration Features**
- **Customer Analytics** - Track customer behavior and preferences
- **Inventory Management** - Real-time stock levels and product data
- **Personalized Recommendations** - ML-powered product suggestions
- **Advanced Reporting** - Custom analytics dashboard
- **API Integration** - RESTful communication with Django backend

---

## 🔧 **Configuration**

### **Theme Settings**
Access via Shopify Admin → Online Store → Themes → Customize:
- **Colors & Typography** - Brand customization
- **Layout Options** - Header, footer, product grids
- **Product Display** - Card styles, image settings
- **Cart & Checkout** - Drawer vs page cart options
- **SEO & Social** - Meta tags, social sharing

### **Django Integration Settings**
Located in `assets/django-integration.js`:
```javascript
// Configuration
this.baseUrl = 'http://localhost:8000/api'; // Django API URL
this.isDevelopment = true; // Development mode
```

---

## 📊 **Custom Sections**

### **Django Products Section**
A custom section that displays products from your Django backend:

**Features:**
- Real-time product data from Django API
- Inventory levels and pricing
- Customizable grid layout
- Error handling and loading states
- Responsive design matching Crave theme

**Usage:**
1. Go to Shopify Admin → Online Store → Themes → Customize
2. Add Section → Django Products
3. Configure title, number of products, color scheme
4. Save and preview

---

## 🔗 **API Endpoints**

Your Django backend should provide these endpoints:

```
GET /api/products/featured/     # Featured products
GET /api/customers/sync/        # Customer data sync
POST /api/analytics/page-view/  # Page view tracking
POST /api/analytics/add-to-cart/ # Cart event tracking
```

See `DJANGO_BACKEND_INTEGRATION.md` for complete API documentation.

---

## 🎨 **Customization**

### **Adding Custom Sections**
1. Create new `.liquid` file in `sections/`
2. Include Django integration if needed:
```liquid
<script>
  // Access Django API
  const data = await window.djangoIntegration.makeRequest('/api/endpoint/');
</script>
```

### **Styling**
- **Global Styles**: Edit `assets/base.css`
- **Component Styles**: Edit `assets/component-*.css`
- **Custom CSS**: Add via theme settings or section styles

### **JavaScript**
- **Global JS**: Edit `assets/global.js`
- **Component JS**: Edit specific component files
- **Django Integration**: Extend `assets/django-integration.js`

---

## 🚀 **Deployment**

### **Development Workflow**
```bash
# 1. Start Django backend
cd "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_backend"
python manage.py runserver

# 2. Start Shopify theme development
cd "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_frontend"
start-theme-dev.bat
```

### **Production Deployment**
```bash
# Push theme to Shopify
shopify theme push --unpublished

# Publish theme
shopify theme publish
```

### **Django Backend Deployment**
Update API URLs in `django-integration.js` for production:
```javascript
this.baseUrl = 'https://your-django-backend.com/api';
```

---

## 🔐 **Security**

### **CORS Configuration**
Ensure Django backend allows requests from your Shopify store:
```python
# Django settings.py
CORS_ALLOWED_ORIGINS = [
    "https://7fa66c-ac.myshopify.com",
    "http://127.0.0.1:9292",  # Local development
]
```

### **API Authentication**
For production, implement token-based authentication:
```javascript
// In django-integration.js
headers: {
    'Authorization': 'Bearer ' + apiToken,
    'Content-Type': 'application/json',
}
```

---

## 📈 **Analytics & Tracking**

### **Automatic Tracking**
The theme automatically tracks:
- **Page Views** - All page visits with referrer data
- **Customer Actions** - Login, registration, profile updates
- **Cart Events** - Add to cart, remove from cart, checkout
- **Form Submissions** - Contact forms, newsletter signups

### **Custom Events**
Add custom tracking:
```javascript
// Track custom event
window.djangoIntegration.makeRequest('/api/analytics/custom-event/', 'POST', {
    event_type: 'product_view',
    product_id: productId,
    customer_id: customerId
});
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**Django Integration Not Working:**
1. Check Django server is running on port 8000
2. Verify CORS settings in Django
3. Check browser console for JavaScript errors

**Theme Not Loading:**
1. Run `shopify theme check` for errors
2. Check Shopify CLI is authenticated
3. Verify store URL in batch file

**Styles Not Applied:**
1. Clear browser cache
2. Check CSS file paths in theme.liquid
3. Verify asset compilation

### **Debug Mode**
Enable debug logging:
```javascript
// In django-integration.js
console.log('Django Integration Debug:', data);
```

---

## 📚 **Resources**

- **Shopify Theme Development**: https://shopify.dev/docs/themes
- **Liquid Documentation**: https://shopify.dev/docs/api/liquid
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Crave Theme Support**: Contact theme developer

---

## 🎯 **Summary**

You now have a **production-ready Crave theme** with **sophisticated Django integration**:

### **What's Included:**
- ✅ Complete Crave theme (premium Shopify theme)
- ✅ Django backend integration with real-time sync
- ✅ Customer analytics and tracking
- ✅ Custom Django-powered sections
- ✅ Development tools and batch files
- ✅ Comprehensive documentation

### **Ready to Use:**
1. **Start Development**: Run `start-theme-dev.bat`
2. **Customize Theme**: Use Shopify theme editor
3. **Add Django Sections**: Use the custom Django Products section
4. **Deploy**: Push to Shopify when ready

**Your Crave theme is now enhanced with Django backend capabilities!** 🚀
