# 🔗 **Django Backend Integration for Shopify Theme**

This guide explains how to connect your Shopify theme (`lavish_frontend`) to the Django backend (`lavish_backend`) to use the synced Shopify data.

---

## 📋 **Architecture Overview**

```
┌─────────────────────┐
│   Shopify Store     │
│  (Data Source)      │
└──────────┬──────────┘
           │
           │ GraphQL API
           ▼
┌─────────────────────┐
│  Django Backend     │
│  (Data Layer)       │
│  - Products         │
│  - Customers        │
│  - Orders           │
│  - Inventory        │
│  - Shipping         │
└──────────┬──────────┘
           │
           │ REST/GraphQL API
           ▼
┌─────────────────────┐
│  Shopify Theme      │
│  (Frontend)         │
│  - Display Data     │
│  - Custom Features  │
└─────────────────────┘
```

---

## 🎯 **Integration Options**

### **Option 1: Theme App Extension (Recommended)**
Use Shopify's Theme App Extension to inject custom data from Django backend into your theme.

### **Option 2: Custom Liquid + API Calls**
Use Liquid templates with JavaScript to fetch data from Django REST API.

### **Option 3: Proxy App**
Set up a Shopify app proxy to route requests through Django backend.

---

## 🚀 **Step-by-Step Setup**

### **1. Install Shopify CLI**

```bash
# Install Shopify CLI (if not already installed)
npm install -g @shopify/cli @shopify/theme

# Verify installation
shopify version
```

### **2. Authenticate with Your Store**

```bash
cd "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_frontend"

# Login to Shopify
shopify auth login --store 7fa66c-ac.myshopify.com
```

### **3. Start Development Server**

```bash
# Start local development server
shopify theme dev --store 7fa66c-ac.myshopify.com

# This will:
# - Upload theme as development theme
# - Start local server at http://127.0.0.1:9292
# - Hot reload changes
```

### **4. Create Django REST API Endpoints**

Your Django backend needs to expose REST API endpoints for the theme to consume.

**Create in `lavish_backend/api/` directory:**

```python
# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'collections', views.CollectionViewSet)
router.register(r'inventory', views.InventoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('featured-products/', views.FeaturedProductsView.as_view()),
    path('product/<str:handle>/', views.ProductDetailView.as_view()),
]
```

### **5. Enable CORS for Theme Access**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

# Allow your Shopify store to access the API
CORS_ALLOWED_ORIGINS = [
    "https://7fa66c-ac.myshopify.com",
    "http://127.0.0.1:9292",  # Local development
]
```

### **6. Create Theme Snippets for API Integration**

**Create `snippets/django-api.liquid`:**

```liquid
{% comment %}
  Django Backend API Integration
  Usage: {% render 'django-api' %}
{% endcomment %}

<script>
  const DJANGO_API_URL = 'http://127.0.0.1:8000/api';
  
  // Fetch products from Django backend
  async function fetchDjangoProducts() {
    try {
      const response = await fetch(`${DJANGO_API_URL}/products/`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching products:', error);
      return [];
    }
  }
  
  // Fetch inventory levels
  async function fetchInventoryLevels(productId) {
    try {
      const response = await fetch(`${DJANGO_API_URL}/inventory/?product=${productId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching inventory:', error);
      return null;
    }
  }
  
  // Make functions globally available
  window.DjangoAPI = {
    fetchProducts: fetchDjangoProducts,
    fetchInventory: fetchInventoryLevels
  };
</script>
```

### **7. Create Custom Section Using Django Data**

**Create `sections/django-products.liquid`:**

```liquid
{% comment %}
  Custom Products Section powered by Django Backend
{% endcomment %}

<div class="django-products-section" data-section-id="{{ section.id }}">
  <div class="container">
    <h2>{{ section.settings.heading }}</h2>
    
    <div id="django-products-grid" class="products-grid">
      <div class="loading">Loading products from Django backend...</div>
    </div>
  </div>
</div>

{% render 'django-api' %}

<script>
  document.addEventListener('DOMContentLoaded', async function() {
    const grid = document.getElementById('django-products-grid');
    
    // Fetch products from Django
    const products = await window.DjangoAPI.fetchProducts();
    
    if (products.length === 0) {
      grid.innerHTML = '<p>No products available</p>';
      return;
    }
    
    // Render products
    grid.innerHTML = products.map(product => `
      <div class="product-card">
        <img src="${product.image_url}" alt="${product.title}">
        <h3>${product.title}</h3>
        <p class="price">$${product.price}</p>
        <p class="inventory">Stock: ${product.inventory_quantity}</p>
        <a href="/products/${product.handle}" class="button">View Product</a>
      </div>
    `).join('');
  });
</script>

{% schema %}
{
  "name": "Django Products",
  "settings": [
    {
      "type": "text",
      "id": "heading",
      "label": "Heading",
      "default": "Featured Products from Django"
    }
  ],
  "presets": [
    {
      "name": "Django Products"
    }
  ]
}
{% endschema %}

<style>
  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
  }
  
  .product-card {
    border: 1px solid #ddd;
    padding: 1rem;
    border-radius: 8px;
  }
  
  .product-card img {
    width: 100%;
    height: auto;
  }
  
  .loading {
    text-align: center;
    padding: 2rem;
  }
</style>
```

---

## 🔧 **Django Backend Setup**

### **1. Create API App**

```bash
cd "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_backend"
python manage.py startapp api
```

### **2. Install Django REST Framework**

```bash
pip install djangorestframework django-cors-headers
```

### **3. Create Serializers**

**Create `api/serializers.py`:**

```python
from rest_framework import serializers
from products.models import ShopifyProduct, ShopifyProductVariant
from inventory.models import ShopifyInventoryLevel

class ProductVariantSerializer(serializers.ModelSerializer):
    inventory_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopifyProductVariant
        fields = ['id', 'title', 'price', 'sku', 'inventory_quantity']
    
    def get_inventory_quantity(self, obj):
        if hasattr(obj, 'inventory_item'):
            levels = obj.inventory_item.levels.all()
            return sum(level.available for level in levels)
        return 0

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopifyProduct
        fields = ['id', 'title', 'handle', 'description', 'product_type', 
                  'vendor', 'image_url', 'variants']
    
    def get_image_url(self, obj):
        image = obj.images.first()
        return image.src if image else None
```

### **4. Create API Views**

**Create `api/views.py`:**

```python
from rest_framework import viewsets, generics
from rest_framework.response import Response
from products.models import ShopifyProduct
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShopifyProduct.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'handle'

class FeaturedProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        # Return products with available inventory
        return ShopifyProduct.objects.filter(
            status='active'
        )[:12]
```

---

## 📦 **Deployment Workflow**

### **Development:**
```bash
# Terminal 1: Django Backend
cd "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_backend"
python manage.py runserver

# Terminal 2: Shopify Theme
cd "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_frontend"
shopify theme dev --store 7fa66c-ac.myshopify.com
```

### **Push Theme to Shopify:**
```bash
# Upload as unpublished theme
shopify theme push --unpublished

# Or update existing theme
shopify theme push
```

### **Publish Theme:**
```bash
shopify theme publish
```

---

## 🔐 **Security Considerations**

1. **API Authentication**: Add token-based auth for production
2. **CORS**: Restrict to your Shopify domain only
3. **Rate Limiting**: Implement rate limiting on API endpoints
4. **HTTPS**: Use HTTPS for production API
5. **Environment Variables**: Store API URLs in theme settings

---

## 📊 **Data Flow Example**

```javascript
// 1. Theme loads
// 2. JavaScript fetches from Django API
fetch('http://127.0.0.1:8000/api/products/')
  .then(res => res.json())
  .then(products => {
    // 3. Display products with real-time inventory
    products.forEach(product => {
      // Show product with Django-managed data
    });
  });
```

---

## ✅ **Next Steps**

1. ✅ Set up Django REST API endpoints
2. ✅ Install and configure CORS
3. ✅ Create theme sections using Django data
4. ✅ Test locally with `shopify theme dev`
5. ✅ Push theme to Shopify
6. ✅ Deploy Django backend to production
7. ✅ Update API URLs for production

---

## 🆘 **Troubleshooting**

**CORS Errors:**
- Check `CORS_ALLOWED_ORIGINS` in Django settings
- Ensure Django backend is running

**API Not Responding:**
- Verify Django server is running on port 8000
- Check firewall settings

**Theme Not Loading:**
- Run `shopify theme check` for errors
- Check browser console for JavaScript errors

---

**Ready to integrate? Follow the steps above!** 🚀
