# 📦 Lavish Library - Complete Package Information

## 🎯 What's Included

This package contains the complete Lavish Library e-commerce system ready for deployment on another machine.

### 📁 Package Contents
```
Lavish-Library/
├── 📋 SETUP_INSTRUCTIONS.md         # Complete setup guide
├── 📋 PACKAGE_INFO.md               # This file
├── 🚀 START_SERVER_PORT_8003.bat    # Start servers on port 8003
├── 🚀 QUICK_START_UV.bat            # Quick setup with uv
├── 🚀 START_BOTH_SERVERS.bat        # Original starter (port 8000)
├── 📄 .env                          # Frontend Shopify config
├── 📄 requirements.txt              # Root dependencies
├── 
├── app/
│   ├── lavish_backend/              # 🐍 Django Backend
│   │   ├── 📄 .env                  # Backend environment variables
│   │   ├── 📄 requirements.txt      # Backend dependencies
│   │   ├── 📄 manage.py             # Django management script
│   │   ├── 🗄️ lavish_library.db     # Pre-populated SQLite database
│   │   ├── 📁 core/                 # Django core settings
│   │   ├── 📁 accounts/             # User management system
│   │   ├── 📁 customers/            # Customer data management
│   │   ├── 📁 products/             # Product management
│   │   ├── 📁 orders/               # Order processing
│   │   ├── 📁 inventory/            # Inventory tracking
│   │   ├── 📁 shipping/             # Shipping logic
│   │   ├── 📁 subscriptions/        # Subscription management
│   │   ├── 📁 shopify_integration/  # Shopify API integration
│   │   ├── 📁 api/                  # REST API endpoints
│   │   ├── 📁 static/               # Static files
│   │   └── 📁 templates/            # Django templates
│   │
│   └── lavish_frontend/             # 🛍️ Shopify Liquid Theme
│       ├── 📁 sections/             # Liquid sections
│       │   ├── enhanced-account.liquid  # ⭐ Main customer account system
│       │   └── header.liquid        # Site header
│       ├── 📁 layout/               # Theme layouts
│       ├── 📁 templates/            # Page templates
│       ├── 📁 assets/               # CSS/JS/Images
│       ├── 📁 snippets/             # Reusable components
│       ├── 📁 config/               # Theme configuration
│       └── 📁 .shopify/             # Shopify CLI config
```

## 🚀 Quick Start Options

### Option 1: Automated Setup (Recommended)
```bash
# Run the quick start script
QUICK_START_UV.bat
```
This will:
- Install uv package manager
- Create virtual environment
- Install all dependencies
- Run migrations
- Start Django on port 8003

### Option 2: Manual Setup
```bash
# Follow the detailed instructions in:
SETUP_INSTRUCTIONS.md
```

### Option 3: Use Existing Scripts
```bash
# Start on port 8003
START_SERVER_PORT_8003.bat

# Start on port 8000 (original)
START_BOTH_SERVERS.bat
```

## 🔧 System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

### Required Tools
1. **uv** - Modern Python package manager
2. **Shopify CLI** - For theme development
3. **Git** - For version control (optional)

## 🌐 Default Ports & URLs

### Development Servers
- **Django Backend**: `http://127.0.0.1:8003`
- **Django Admin**: `http://127.0.0.1:8003/admin/`
- **Django API**: `http://127.0.0.1:8003/api/`
- **Shopify Theme**: `http://127.0.0.1:9292`

### Admin Access
- **Username**: `admin`
- **Password**: `vanity007`

## 🎨 Key Features Included

### Enhanced Customer Account System
- ✅ **Multi-tab Interface**: Overview, Profile, MFA, Password, Addresses, Payment, Subscriptions, Orders
- ✅ **Professional Modals**: All interactions use custom modals with consistent styling
- ✅ **Address Management**: Full CRUD operations with shipping integration
- ✅ **Subscription Management**: Pause, modify, cancel subscriptions with confirmation dialogs
- ✅ **Order Management**: View order details, edit upcoming orders
- ✅ **MFA Security**: Two-factor authentication setup and verification
- ✅ **Privacy Features**: Address censoring for security
- ✅ **Responsive Design**: Mobile-first approach with professional UI/UX

### Backend Features
- ✅ **Django Admin**: Fully configured admin interface
- ✅ **REST API**: Complete API for frontend integration
- ✅ **Shopify Integration**: Real-time sync with Shopify store
- ✅ **Database**: Pre-populated with sample data
- ✅ **Authentication**: User management and security
- ✅ **Logging**: Comprehensive logging system

### Frontend Features
- ✅ **Shopify Liquid Theme**: Professional e-commerce theme
- ✅ **Custom Account Pages**: Enhanced customer account experience
- ✅ **Modal System**: Professional modal dialogs throughout
- ✅ **Toast Notifications**: Non-intrusive user feedback
- ✅ **Consistent Styling**: Menu hover colors and professional design

## 🔗 Integration Details

### Django ↔ Shopify Integration
The system includes bidirectional integration:
- **Customer Data Sync**: Automatic synchronization of customer information
- **Order Processing**: Real-time order updates between systems
- **Product Management**: Inventory and product data synchronization
- **Subscription Handling**: Advanced subscription management

### API Endpoints
- `GET/POST /api/customers/` - Customer management
- `GET/POST /api/orders/` - Order processing
- `GET/POST /api/products/` - Product synchronization
- `GET/POST /api/inventory/` - Inventory updates
- `GET/POST /api/subscriptions/` - Subscription management

## 🛡️ Security Features

### Environment Variables
All sensitive data is stored in `.env` files:
- Shopify API credentials
- Django secret keys
- Database configurations
- Third-party service keys

### Authentication
- Django admin authentication
- Shopify store authentication
- MFA support for customers
- Secure session management

## 📊 Database Information

### Pre-populated Data
The included SQLite database contains:
- **Sample customers** with addresses and orders
- **Product catalog** synced with Shopify
- **Order history** with various statuses
- **Subscription data** for testing
- **Admin user** (admin/vanity007)

### Models Included
- User accounts and profiles
- Customer data and addresses
- Product and inventory information
- Order and subscription management
- Shipping and payment data

## 🔧 Customization Points

### Key Files for Modification
- **Customer Account UI**: `app/lavish_frontend/sections/enhanced-account.liquid`
- **Django Settings**: `app/lavish_backend/core/settings.py`
- **API Configuration**: `app/lavish_backend/api/`
- **Theme Styling**: `app/lavish_frontend/assets/`
- **Database Models**: `app/lavish_backend/*/models.py`

### Environment Configuration
Update these files for your environment:
- `app/lavish_backend/.env` - Backend configuration
- `.env` - Frontend Shopify configuration

## 📞 Support & Documentation

### Included Documentation
- `SETUP_INSTRUCTIONS.md` - Complete setup guide
- `app/lavish_frontend/*.md` - Feature documentation
- Inline code comments throughout

### Troubleshooting
Common issues and solutions are covered in the setup instructions.

---

## 🎯 Ready to Deploy!

This package is production-ready and includes everything needed to run the Lavish Library e-commerce system on any compatible machine. Simply extract, follow the setup instructions, and you'll have a fully functional system running on localhost:8003.

**Happy coding! 🚀**
