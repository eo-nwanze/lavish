# Lavish Library - Complete Setup Instructions

## 📦 Project Overview
This is a complete Lavish Library e-commerce system with:
- **Django Backend** (API + Admin) - Port 8000
- **Shopify Liquid Frontend** (Theme Development) - Port 9292
- **Integrated Customer Account System** with enhanced UI/UX

## 🚀 Quick Start (Localhost Port 8003)

### Prerequisites
1. **Python 3.11+** installed
2. **Node.js 18+** installed
3. **Shopify CLI** installed
4. **uv** package manager installed

### Step 1: Install uv (if not installed)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Extract and Navigate
```bash
# Extract the zip file to your desired location
cd path/to/extracted/Lavish-Library
```

### Step 3: Setup Django Backend (Port 8003)
```bash
# Navigate to backend
cd app/lavish_backend

# Create virtual environment with uv
uv venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies with uv
uv pip install django==4.2.23
uv pip install djangorestframework==3.16.0
uv pip install django-cors-headers==4.7.0
uv pip install python-dotenv==1.0.0
uv pip install requests==2.31.0
uv pip install django-environ==0.12.0
uv pip install whitenoise==6.9.0

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start Django on port 8003
python manage.py runserver 127.0.0.1:8003
```

### Step 4: Setup Shopify Frontend (Separate Terminal)
```bash
# Navigate to frontend
cd app/lavish_frontend

# Install Shopify CLI (if not installed)
npm install -g @shopify/cli @shopify/theme

# Start Shopify theme development server
shopify theme dev --store 7fa66c-ac.myshopify.com --port 9292
```

## 🔧 Environment Configuration

### Backend Environment (.env)
Located at: `app/lavish_backend/.env`
```env
# Django Settings
SECRET_KEY=django-insecure-g!@oi#!t-u06qml(#6jm6=b!f-=f^%i6yb@nc+xrf%^2o0fei6
DEBUG=True

# Shopify API Configuration
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_ACCESS_TOKEN=your_access_token_here
SHOPIFY_API_VERSION=2025-01

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# Logging
LOG_LEVEL=DEBUG
```

### Frontend Environment (.env)
Located at: `root/.env`
```env
SHOPIFY_SHOP_URL=your-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_access_token_here
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
```

## 🌐 Access URLs

### Development Servers
- **Django Backend**: http://127.0.0.1:8003
- **Django Admin**: http://127.0.0.1:8003/admin/
- **Django API**: http://127.0.0.1:8003/api/
- **Shopify Theme**: http://127.0.0.1:9292

### Admin Credentials
- **Username**: admin
- **Password**: vanity007

## 📁 Project Structure
```
Lavish-Library/
├── .env                          # Frontend Shopify config
├── requirements.txt              # Root dependencies
├── START_BOTH_SERVERS.bat       # Windows batch starter
├── app/
│   ├── lavish_backend/          # Django Backend
│   │   ├── .env                 # Backend environment
│   │   ├── manage.py            # Django management
│   │   ├── core/                # Django core settings
│   │   ├── accounts/            # User management
│   │   ├── customers/           # Customer data
│   │   ├── products/            # Product management
│   │   ├── orders/              # Order processing
│   │   ├── inventory/           # Inventory tracking
│   │   ├── shipping/            # Shipping logic
│   │   ├── subscriptions/       # Subscription management
│   │   ├── shopify_integration/ # Shopify API integration
│   │   └── lavish_library.db    # SQLite database
│   │
│   └── lavish_frontend/         # Shopify Liquid Theme
│       ├── sections/            # Liquid sections
│       │   ├── enhanced-account.liquid  # Main account system
│       │   └── header.liquid    # Site header
│       ├── layout/              # Theme layouts
│       ├── templates/           # Page templates
│       ├── assets/              # CSS/JS/Images
│       ├── snippets/            # Reusable components
│       └── config/              # Theme configuration
```

## 🛠️ Development Commands

### Django Backend Commands
```bash
cd app/lavish_backend

# Start development server (port 8003)
python manage.py runserver 127.0.0.1:8003

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

### Shopify Frontend Commands
```bash
cd app/lavish_frontend

# Start theme development
shopify theme dev --store 7fa66c-ac.myshopify.com

# Deploy to theme
shopify theme push

# Pull latest theme
shopify theme pull

# Check theme
shopify theme check
```

## 🔗 API Integration

### Django-Shopify Integration
The backend provides REST APIs that integrate with Shopify:

- **Customer Management**: `/api/customers/`
- **Order Processing**: `/api/orders/`
- **Product Sync**: `/api/products/`
- **Inventory Updates**: `/api/inventory/`
- **Subscription Management**: `/api/subscriptions/`

### Frontend Integration
The Shopify theme includes JavaScript that communicates with Django:
```javascript
// Example API call from frontend
if (window.djangoIntegration) {
  window.djangoIntegration.makeRequest('/api/customers/', 'GET', data);
}
```

## 🎨 Enhanced Features

### Customer Account System
- **Multi-tab Interface**: Overview, Profile, MFA, Password, Addresses, Payment, Subscriptions, Orders
- **Modal System**: Professional modals for all interactions
- **Address Management**: Full CRUD with shipping integration
- **Subscription Management**: Pause, modify, cancel subscriptions
- **Order Management**: View details, edit upcoming orders
- **MFA Security**: Two-factor authentication setup

### UI/UX Enhancements
- **Consistent Color Scheme**: Menu hover colors throughout
- **Responsive Design**: Mobile-first approach
- **Professional Modals**: Confirmation dialogs and wizards
- **Toast Notifications**: Non-intrusive user feedback
- **Privacy Features**: Censored address display

## 🚨 Troubleshooting

### Common Issues

1. **Port 8003 Already in Use**
   ```bash
   # Find process using port
   netstat -ano | findstr :8003
   # Kill process (Windows)
   taskkill /PID <PID> /F
   ```

2. **Shopify CLI Authentication**
   ```bash
   shopify auth logout
   shopify auth login
   ```

3. **Django Database Issues**
   ```bash
   python manage.py migrate --run-syncdb
   ```

4. **Missing Dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

### Environment Variables
Ensure all `.env` files are properly configured with your Shopify store credentials.

## 📞 Support

### Key Files for Customization
- **Customer Account UI**: `app/lavish_frontend/sections/enhanced-account.liquid`
- **Django Settings**: `app/lavish_backend/core/settings.py`
- **API Endpoints**: `app/lavish_backend/api/`
- **Database Models**: `app/lavish_backend/*/models.py`

### Development Notes
- Database is pre-populated with sample data
- Admin interface is fully configured
- All modals and forms are functional
- Shopify integration is active and tested

---

## 🎯 Quick Start Summary

1. **Install uv**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. **Extract project** to desired location
3. **Backend**: `cd app/lavish_backend && uv venv && .venv\Scripts\activate && uv pip install django djangorestframework django-cors-headers python-dotenv requests && python manage.py runserver 127.0.0.1:8003`
4. **Frontend**: `cd app/lavish_frontend && shopify theme dev --store 7fa66c-ac.myshopify.com`
5. **Access**: http://127.0.0.1:8003 (Django) & http://127.0.0.1:9292 (Shopify)

**Admin Login**: admin / vanity007
