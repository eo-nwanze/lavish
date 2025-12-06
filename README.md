<<<<<<< HEAD
# Lavish Library - Shopify Customer Account System

A comprehensive customer account management system integrating Shopify themes with Django backend.

## Project Structure

```
Lavish Library/
├── app/
│   ├── lavish_frontend/         # Shopify theme files
│   │   ├── assets/              # CSS, JS, images
│   │   ├── config/              # Theme configuration
│   │   ├── layout/              # Theme layouts
│   │   ├── sections/            # Shopify sections
│   │   ├── snippets/            # Reusable theme snippets
│   │   └── templates/           # Page templates
│   └── lavish_backend/          # Django backend
│       ├── accounts/            # User authentication
│       ├── api/                 # REST API endpoints
│       ├── customers/           # Customer management
│       ├── inventory/           # Inventory tracking
│       ├── locations/           # Location data (countries, states, cities)
│       ├── orders/              # Order processing
│       ├── payments/            # Payment methods
│       ├── products/            # Product catalog
│       ├── shipping/            # Shipping management
│       ├── shopify_integration/ # Shopify API integration
│       └── subscriptions/       # Subscription management
└── project_req_data/            # Project requirements and data

## Features

### Frontend (Shopify Theme)
- **Enhanced Customer Account Interface**
  - Mobile-first responsive design
  - Tab-based navigation (Subscriptions, Overview, Addresses, Payment Methods, Personal Info)
  - Real-time data sync with Django backend
  - Modal-based wizards for data entry
  - MFA verification system
  
### Backend (Django)
- **REST API** for frontend integration
- **Location Management** - Countries, states, cities, phone codes
- **Customer Management** - Profiles, addresses, payment methods
- **Order Processing** - Order tracking and fulfillment
- **Subscription System** - Recurring billing management
- **Shopify Integration** - Webhook handlers and API sync

## Tech Stack

- **Frontend**: Shopify Liquid, JavaScript (ES6+), CSS3
- **Backend**: Django 4.2.23, Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production ready)
- **APIs**: Shopify Admin API, Custom REST APIs
- **Deployment**: Cloudflare Tunnels

## Installation

### Prerequisites
- Python 3.8+
- Shopify CLI
- Git

### Backend Setup

1. Create virtual environment:
```bash
python -m venv lavish_backend_env
```

2. Activate virtual environment:
```bash
# Windows
.\lavish_backend_env\Scripts\activate

# macOS/Linux
source lavish_backend_env/bin/activate
```

3. Install dependencies:
```bash
cd app/lavish_backend
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start backend server:
```bash
python manage.py runserver 8003
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd app/lavish_frontend
```

2. Start Shopify development server:
```bash
shopify theme dev --port 9292
```

## Configuration

### Environment Variables

Create a `.env` file in `app/lavish_backend/core/`:

```env
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_ACCESS_TOKEN=your_access_token
SHOPIFY_API_VERSION=2025-01
DEBUG=True
SECRET_KEY=your_secret_key
```

### Production Deployment

The system is configured for deployment via Cloudflare Tunnels:
- Frontend: `viewing.endevops.net:9292`
- Backend: `lavish-backend.endevops.net:8003`

Update `app/lavish_backend/core/settings.py`:
- `ALLOWED_HOSTS` - Add your production domains
- `CORS_ALLOWED_ORIGINS` - Configure CORS for your domains
- `DEBUG = False` for production

## API Endpoints

### Location API
- `GET /api/locations/countries/` - List all countries
- `GET /api/locations/countries/{id}/states/` - Get states by country
- `GET /api/locations/states/{id}/cities/` - Get cities by state
- `GET /api/locations/phone_codes/` - Get phone country codes

### Customer API
- `POST /api/customers/addresses/create/` - Create address
- `PUT /api/customers/addresses/update/` - Update address
- `DELETE /api/customers/addresses/delete/` - Delete address
- `POST /api/customers/payment-methods/create/` - Add payment method
- `DELETE /api/customers/payment-methods/delete/` - Remove payment method

## Development Scripts

- `START_BOTH_SERVERS.bat` - Start both backend and frontend servers
- `START_SERVER_PORT_8003.bat` - Start backend only
- `QUICK_START_UV.bat` - Quick start with UV package manager

## Recent Updates

### Mobile Optimization (November 2025)
- ✅ Full-width mobile treatment for all account tabs
- ✅ Optimized phone input fields and country code dropdowns
- ✅ Fixed sidebar responsive behavior
- ✅ API-driven country/state/city loading
- ✅ Production deployment configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Proprietary - All rights reserved

## Support

For support, contact the development team or create an issue in the repository.
=======
# lavish
>>>>>>> 223491a2746e2e7b5c7c2f5136f8c736e40a8192
