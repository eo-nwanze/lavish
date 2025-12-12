# 📍 LOCATION SYSTEM - DETAILED EXPLANATION

## 🎯 **IMPORTANT DISTINCTION**

There are **TWO SEPARATE** location systems in your Django backend:

1. **Geographic Locations** (`locations` app) - Countries, States, Cities
2. **Inventory/Fulfillment Locations** (`inventory` app) - Warehouses

**This document covers Geographic Locations.**

---

## 📊 **CURRENT LOCATION DATA**

### **Summary**
- **Countries**: 8
- **States/Provinces**: 41
- **Cities**: 759

### **Complete List of Countries**

| Flag | Country | ISO Code | Phone Code | Currency | States | Cities |
|------|---------|----------|------------|----------|--------|--------|
| 🇦🇺 | Australia | AU | +61 | AUD | 4 | 20 |
| 🇨🇦 | Canada | CA | +1 | CAD | 4 | ~100 |
| 🇫🇷 | France | FR | +33 | EUR | 4 | 20 |
| 🇩🇪 | Germany | DE | +49 | EUR | 4 | 21 |
| 🇮🇳 | India | IN | +91 | INR | 28 | ~500 |
| 🇯🇵 | Japan | JP | +81 | JPY | 1 | 47 |
| 🇬🇧 | United Kingdom | GB | +44 | GBP | 4 | 20 |
| 🇺🇸 | United States | US | +1 | USD | 4 | 20 |

---

## 🏗️ **HOW LOCATIONS WORK**

### **1. Data Source**

**❌ NOT from Shopify API**  
**✅ Manually configured in Django**

The location data is:
- **Stored locally** in Django's SQLite database
- **Pre-populated** using a Django management command
- **Not synced** with Shopify (separate from Shopify locations)
- **Independent** of Shopify's geographic data

---

## 🗄️ **DATABASE STRUCTURE**

### **Three Models (Hierarchical)**

```
Country (8 records)
  ├── State (41 records)
  │     └── City (759 records)
```

### **1. Country Model**

**Location**: `app/lavish_backend/locations/models.py`

```python
class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    iso_code = models.CharField(max_length=2, unique=True)      # AU, US, GB
    iso3_code = models.CharField(max_length=3, unique=True)     # AUS, USA, GBR
    phone_code = models.CharField(max_length=10)                # +61, +1, +44
    currency = models.CharField(max_length=3, blank=True)       # AUD, USD, GBP
    currency_symbol = models.CharField(max_length=5, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    flag_emoji = models.CharField(max_length=10, blank=True)    # 🇦🇺, 🇺🇸, 🇬🇧
```

**Example Record:**
```python
Country(
    name='Australia',
    iso_code='AU',
    iso3_code='AUS',
    phone_code='61',
    currency='AUD',
    currency_symbol='A$',
    timezone='Australia/Sydney',
    flag_emoji='🇦🇺'
)
```

### **2. State Model**

```python
class State(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    state_code = models.CharField(max_length=10, blank=True)    # NSW, CA, TX
```

**Example Record:**
```python
State(
    name='New South Wales',
    country=<Country: Australia>,
    state_code='NSW'
)
```

### **3. City Model**

```python
class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
```

**Example Record:**
```python
City(
    name='Sydney',
    state=<State: New South Wales>,
    latitude=-33.8688,
    longitude=151.2093
)
```

---

## 🔧 **HOW DATA IS POPULATED**

### **Method 1: Management Command (Initial Setup)**

**File**: `app/lavish_backend/locations/management/commands/populate_countries.py`

**Run Command:**
```bash
cd app/lavish_backend
python manage.py populate_countries
```

**What it does:**
1. Creates 8 countries with full details
2. Creates states/provinces for each country
3. Creates major cities for each state
4. Uses `get_or_create()` to avoid duplicates
5. Prints progress messages

**Output Example:**
```
Created country: Australia
  Created state: New South Wales
    Created city: Sydney
    Created city: Newcastle
    Created city: Wollongong
  Created state: Victoria
    Created city: Melbourne
    Created city: Geelong
...
Successfully populated countries, states, and cities!
```

### **Current Data Sample**

**Australia (4 states, 20 cities):**
```python
{
    'name': 'Australia',
    'states': [
        {
            'name': 'New South Wales',
            'state_code': 'NSW',
            'cities': ['Sydney', 'Newcastle', 'Wollongong', 'Central Coast', 'Blue Mountains']
        },
        {
            'name': 'Victoria',
            'cities': ['Melbourne', 'Geelong', 'Ballarat', 'Bendigo', 'Warrnambool']
        },
        {
            'name': 'Queensland',
            'cities': ['Brisbane', 'Gold Coast', 'Sunshine Coast', 'Cairns', 'Townsville']
        },
        {
            'name': 'Western Australia',
            'cities': ['Perth', 'Fremantle', 'Mandurah', 'Bunbury', 'Geraldton']
        }
    ]
}
```

**United States (4 states, 20 cities):**
- California: Los Angeles, San Francisco, San Diego, Sacramento, San Jose
- New York: New York City, Buffalo, Rochester, Albany, Syracuse
- Texas: Houston, Dallas, Austin, San Antonio, Fort Worth
- Florida: Miami, Orlando, Tampa, Jacksonville, Tallahassee

---

## 🔌 **DJANGO API ENDPOINTS**

### **Location API** (`/api/locations/`)

**1. Get All Countries**
```
GET /api/locations/countries/
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "Australia",
        "iso_code": "AU",
        "iso3_code": "AUS",
        "phone_code": "61",
        "currency": "AUD",
        "currency_symbol": "A$",
        "timezone": "Australia/Sydney",
        "flag_emoji": "🇦🇺",
        "states": [
            {
                "id": 1,
                "name": "New South Wales",
                "state_code": "NSW",
                "cities": [
                    {
                        "id": 1,
                        "name": "Sydney",
                        "latitude": -33.8688,
                        "longitude": 151.2093
                    },
                    ...
                ]
            },
            ...
        ]
    },
    ...
]
```

**2. Get States for a Country**
```
GET /api/locations/countries/{country_id}/states/
```

**Example:**
```
GET /api/locations/countries/1/states/
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "New South Wales",
        "state_code": "NSW",
        "cities": [
            {"id": 1, "name": "Sydney"},
            {"id": 2, "name": "Newcastle"},
            ...
        ]
    },
    ...
]
```

**3. Get Cities for a State**
```
GET /api/locations/states/{state_id}/cities/
```

**Example:**
```
GET /api/locations/states/1/cities/
```

**Response:**
```json
[
    {"id": 1, "name": "Sydney", "latitude": -33.8688, "longitude": 151.2093},
    {"id": 2, "name": "Newcastle", "latitude": null, "longitude": null},
    ...
]
```

**4. Get Phone Codes**
```
GET /api/locations/phone_codes/
```

**Response:**
```json
[
    {
        "country_id": 1,
        "country_name": "Australia",
        "iso_code": "AU",
        "phone_code": "61",
        "flag_emoji": "🇦🇺"
    },
    ...
]
```

---

## 🎨 **FRONTEND INTEGRATION**

### **How Locations Are Used in Frontend**

The location data is consumed by the Shopify Liquid theme through:

1. **JavaScript File**: `assets/django-integration.js`
2. **Liquid Templates**: Address forms in `enhanced-account.liquid`

---

## 🔄 **COMPLETE FLOW**

### **1. Page Load**

```javascript
// In django-integration.js

class DjangoIntegration {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:8003/api'; // or production URL
        this.countries = [];
        this.phoneCodes = [];
        
        this.init();
    }
    
    init() {
        // Load location data immediately
        this.loadLocationData();
    }
}
```

### **2. Load Location Data**

```javascript
async loadLocationData() {
    // Fetch countries (includes states and cities)
    const countriesData = await this.makeRequest('/locations/countries/');
    this.countries = countriesData;
    console.log(`✅ Loaded ${this.countries.length} countries`);
    
    // Fetch phone codes
    const phoneCodesData = await this.makeRequest('/locations/phone_codes/');
    this.phoneCodes = phoneCodesData;
    console.log(`✅ Loaded ${this.phoneCodes.length} phone codes`);
    
    // Populate dropdowns
    this.populateCountryDropdowns();
}
```

### **3. Populate Dropdowns**

```javascript
populateCountryDropdowns() {
    // Find all country dropdowns
    const countryDropdowns = document.querySelectorAll(
        'select[name="country"], ' +
        'select[id="addr_country"], ' +
        'select[id="edit_addr_country"]'
    );
    
    countryDropdowns.forEach(dropdown => {
        // Clear existing options
        while (dropdown.options.length > 1) {
            dropdown.remove(1);
        }
        
        // Add countries from API
        this.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.id;
            option.textContent = `${country.flag_emoji} ${country.name} (+${country.phone_code})`;
            option.dataset.phoneCode = country.phone_code;
            dropdown.appendChild(option);
        });
        
        // Add change event listener
        dropdown.addEventListener('change', (e) => {
            this.handleCountryChange(e.target);
        });
    });
}
```

### **4. Cascading Dropdowns**

**Country Selection → Load States:**

```javascript
async handleCountryChange(countrySelect) {
    const countryId = countrySelect.value;
    
    // Update phone code dropdown
    this.updatePhoneCode(countrySelect);
    
    // Load states for selected country
    const states = await this.makeRequest(`/locations/countries/${countryId}/states/`);
    
    // Populate state dropdown
    const stateDropdown = document.querySelector('select[name="province"]');
    stateDropdown.innerHTML = '<option value="">Select State...</option>';
    
    states.forEach(state => {
        const option = document.createElement('option');
        option.value = state.id;
        option.textContent = state.name;
        stateDropdown.appendChild(option);
    });
    
    // Add state change listener
    stateDropdown.addEventListener('change', (e) => {
        this.handleStateChange(e.target);
    });
}
```

**State Selection → Load Cities:**

```javascript
async handleStateChange(stateSelect) {
    const stateId = stateSelect.value;
    
    // Load cities for selected state
    const cities = await this.makeRequest(`/locations/states/${stateId}/cities/`);
    
    // Populate city dropdown
    const cityDropdown = document.querySelector('select[name="city"]');
    cityDropdown.innerHTML = '<option value="">Select City...</option>';
    
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city.id;
        option.textContent = city.name;
        cityDropdown.appendChild(option);
    });
}
```

### **5. Phone Code Synchronization**

When country is selected, phone code is automatically updated:

```javascript
updatePhoneCode(countryDropdown) {
    const selectedOption = countryDropdown.options[countryDropdown.selectedIndex];
    const phoneCode = selectedOption.dataset.phoneCode;
    
    // Update phone code dropdown
    const phoneCodeDropdown = document.querySelector('select[name="phone_country_code"]');
    for (let i = 0; i < phoneCodeDropdown.options.length; i++) {
        if (phoneCodeDropdown.options[i].value === `+${phoneCode}`) {
            phoneCodeDropdown.selectedIndex = i;
            break;
        }
    }
    
    // Prepend country code to phone input
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput && !phoneInput.value.startsWith('+')) {
        phoneInput.value = `+${phoneCode} `;
    }
}
```

---

## 🖥️ **FRONTEND HTML EXAMPLE**

### **Address Form in Liquid**

```liquid
<!-- In sections/enhanced-account.liquid -->

<div class="address-form">
    <!-- Country Dropdown -->
    <div class="form-group">
        <label for="addr_country">Country</label>
        <select id="addr_country" name="country" required>
            <option value="">Select Country...</option>
            <!-- Populated by JavaScript -->
        </select>
    </div>
    
    <!-- Phone Code Dropdown (synced with country) -->
    <div class="form-group">
        <label for="addr_country_code">Phone Code</label>
        <select id="addr_country_code" name="phone_country_code">
            <option value="">Select...</option>
            <!-- Populated by JavaScript -->
        </select>
    </div>
    
    <!-- Phone Number Input -->
    <div class="form-group">
        <label for="addr_phone">Phone</label>
        <input type="tel" id="addr_phone" name="phone" placeholder="+61 400 000 000">
    </div>
    
    <!-- State Dropdown (populated after country selection) -->
    <div class="form-group">
        <label for="addr_province">State/Province</label>
        <select id="addr_province" name="province" required disabled>
            <option value="">Select Country First...</option>
        </select>
    </div>
    
    <!-- City Dropdown (populated after state selection) -->
    <div class="form-group">
        <label for="addr_city">City</label>
        <select id="addr_city" name="city" required disabled>
            <option value="">Select State First...</option>
        </select>
    </div>
    
    <!-- Other address fields -->
    <div class="form-group">
        <label for="addr_address1">Street Address</label>
        <input type="text" id="addr_address1" name="address1" required>
    </div>
    
    <div class="form-group">
        <label for="addr_zip">Postal Code</label>
        <input type="text" id="addr_zip" name="zip_code" required>
    </div>
</div>

<script>
// Initialize Django Integration
window.djangoIntegration = new DjangoIntegration();
</script>
```

---

## ⚙️ **DJANGO ADMIN MANAGEMENT**

### **Admin Interface Features**

**File**: `app/lavish_backend/locations/admin.py`

**Features:**
1. **Import/Export** - Upload/download location data via CSV/Excel
2. **Inline Editing** - Edit states within country admin
3. **Search** - Search by name, ISO code, currency
4. **Filtering** - Filter by currency, country
5. **Hierarchical View** - See country → state → city relationships

**Admin URLs:**
- Countries: http://127.0.0.1:8003/admin/locations/country/
- States: http://127.0.0.1:8003/admin/locations/state/
- Cities: http://127.0.0.1:8003/admin/locations/city/

### **Adding New Locations**

**Method 1: Django Admin (GUI)**
1. Go to Django Admin
2. Navigate to Locations → Countries
3. Click "Add Country"
4. Fill in details
5. Add states/cities inline
6. Save

**Method 2: Management Command (Bulk)**
1. Edit `populate_countries.py`
2. Add new country data to `countries_data` list
3. Run: `python manage.py populate_countries`

**Method 3: Django Shell (Manual)**
```python
python manage.py shell

from locations.models import Country, State, City

# Add new country
country = Country.objects.create(
    name='Canada',
    iso_code='CA',
    iso3_code='CAN',
    phone_code='1',
    currency='CAD',
    flag_emoji='🇨🇦'
)

# Add state
state = State.objects.create(
    name='Ontario',
    country=country,
    state_code='ON'
)

# Add city
city = City.objects.create(
    name='Toronto',
    state=state
)
```

**Method 4: Import/Export (CSV)**
1. Go to Django Admin → Locations → Countries
2. Click "Import" button
3. Upload CSV file with format:
```csv
name,iso_code,iso3_code,phone_code,currency,flag_emoji
Canada,CA,CAN,1,CAD,🇨🇦
```
4. Review and confirm import

---

## 📈 **SCALING THE LOCATION DATA**

### **Current Limitations**

- Only 8 countries
- Limited states per country (4-28)
- Limited cities per state (5-50)

### **Expansion Options**

**Option 1: Add More Countries Manually**
- Edit `populate_countries.py`
- Add new countries to `countries_data` list
- Run command

**Option 2: Import from External API**
- Use REST Countries API: https://restcountries.com/
- Create import script
- Automate data fetching

**Option 3: Use Third-Party Package**
- Install: `django-countries` or `django-cities-light`
- Provides 250+ countries, 150k+ cities
- Regular updates

**Option 4: Import from CSV/Excel**
- Download comprehensive location database
- Use Django Admin import feature
- Bulk upload

---

## 🔍 **KEY DIFFERENCES: Geographic vs Shopify Locations**

### **Geographic Locations** (`locations` app)

| Aspect | Details |
|--------|---------|
| **Purpose** | Address forms, shipping destinations |
| **Scope** | Countries, states, cities worldwide |
| **Count** | 8 countries, 41 states, 759 cities |
| **Source** | Manually configured in Django |
| **Models** | `Country`, `State`, `City` |
| **API** | `/api/locations/` |
| **Frontend Use** | Dropdown population, address validation |
| **Shopify Sync** | None - independent system |

### **Shopify Locations** (`inventory` app)

| Aspect | Details |
|--------|---------|
| **Purpose** | Inventory fulfillment, warehouse management |
| **Scope** | Physical warehouse/store locations |
| **Count** | 3 locations (8 Mellifont Street, Laguna, Ogo Print on Demand) |
| **Source** | Synced from Shopify Admin API |
| **Models** | `ShopifyLocation` |
| **API** | `/api/inventory/` |
| **Frontend Use** | Stock availability display |
| **Shopify Sync** | Full bidirectional sync |

---

## 🎯 **USE CASES**

### **1. Address Entry**
```
Customer clicks "Add Address"
  → Modal opens
  → Country dropdown populated with 8 countries
  → Customer selects "Australia"
  → State dropdown populated with 4 Australian states
  → Customer selects "New South Wales"
  → City dropdown populated with 5 NSW cities
  → Customer selects "Sydney"
  → Phone code auto-set to "+61"
  → Address saved to Django → Synced to Shopify
```

### **2. Shipping Calculation**
```
Customer places order
  → Address contains country, state, city
  → Shipping module uses location data
  → Calculate rates based on destination
  → Apply zone-based pricing
```

### **3. Currency Detection**
```
Customer visits site
  → IP geolocation → Country detected
  → Country model has currency field
  → Display prices in local currency (AUD, USD, etc.)
```

### **4. Tax Calculation**
```
Order created
  → Destination country/state extracted
  → Tax rules applied based on location
  → GST for Australia, Sales Tax for US, VAT for EU
```

---

## 🛠️ **TROUBLESHOOTING**

### **Issue: "Error loading countries" in frontend**

**Causes:**
1. Django backend not running
2. CORS not configured
3. Location data not populated
4. Wrong API URL

**Solutions:**
```bash
# Check backend is running
cd app/lavish_backend
python manage.py runserver 8003

# Populate location data
python manage.py populate_countries

# Check CORS settings
# In settings.py:
CORS_ALLOW_ALL_ORIGINS = True  # For development

# Test API directly
curl http://127.0.0.1:8003/api/locations/countries/
```

### **Issue: Dropdowns not populating**

**Causes:**
1. JavaScript not loading
2. API request failing
3. Selector mismatch

**Solutions:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify API calls in Network tab
4. Check `django-integration.js` loaded
5. Verify dropdown IDs match selectors

### **Issue: Phone codes not syncing**

**Causes:**
1. Event listener not attached
2. Dataset not set correctly
3. Dropdown ID mismatch

**Solutions:**
1. Check `updatePhoneCode()` function
2. Verify `dataset.phoneCode` exists
3. Check phone code dropdown selector

---

## 📝 **SUMMARY**

### **What You Need to Know:**

✅ **8 Countries** in database (AU, CA, FR, DE, IN, JP, GB, US)  
✅ **41 States/Provinces** across these countries  
✅ **759 Cities** in total  
✅ **Manually configured** (not from Shopify)  
✅ **Populated via Django command**: `python manage.py populate_countries`  
✅ **Accessed via REST API**: `/api/locations/`  
✅ **Used in frontend**: Cascading address dropdowns  
✅ **Independent system**: Separate from Shopify inventory locations  
✅ **Expandable**: Can add more countries/states/cities easily  
✅ **Admin manageable**: Full CRUD in Django Admin  

### **Data Flow:**

```
Django Database (SQLite)
    ↓
Django Models (Country, State, City)
    ↓
Django REST API (/api/locations/)
    ↓
JavaScript (django-integration.js)
    ↓
Liquid Frontend (Dropdown Population)
    ↓
Customer Interaction (Address Entry)
```

### **NOT Shopify Data:**

- These locations are **NOT** synced from Shopify
- They are **NOT** Shopify's inventory locations
- They are **NOT** automatically updated
- They **DO NOT** appear in Shopify Admin
- They are **ONLY** for Django/Frontend use

---

## 📞 **QUESTIONS?**

**Adding more countries?**  
→ Edit `populate_countries.py` and run the command

**Need all countries?**  
→ Consider installing `django-cities-light` package

**API not working?**  
→ Check Django server running on port 8003

**Frontend not loading?**  
→ Check browser console and Network tab

---

**Last Updated**: December 12, 2025  
**Version**: 1.0  
**File**: `LOCATION_SYSTEM_EXPLAINED.md`

