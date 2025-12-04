/**
 * Django Backend Integration for Lavish Library
 * 
 * This script handles communication between the Shopify theme and Django backend
 * for enhanced customer data management and analytics
 */

class DjangoIntegration {
    constructor() {
        // Detect environment and set appropriate base URL
        if (window.location.hostname === 'localhost' || 
            window.location.hostname === '127.0.0.1' ||
            window.location.hostname.includes('myshopify.com')) {
            this.baseUrl = 'http://127.0.0.1:8003/api'; // Development
        } else {
            this.baseUrl = 'https://lavish-backend.endevops.net/api'; // Production
        }
        
        this.apiKey = null; // Will be set from theme settings
        this.initialized = false;
        this.countries = [];
        this.states = [];
        this.cities = [];
        this.phoneCodes = [];
        
        this.init();
    }
    
    init() {
        // Initialize the integration
        console.log('Django Integration: Initializing...');
        
        // Check if we're in development or production
        this.isDevelopment = window.location.hostname === 'localhost' || 
                            window.location.hostname.includes('myshopify.com');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load location data for forms
        this.loadLocationData();
        
        // Initialize customer tracking if customer is logged in
        if (window.Shopify && window.Shopify.customer) {
            this.trackCustomer(window.Shopify.customer);
        }
        
        this.initialized = true;
        console.log('Django Integration: Initialized successfully');
    }
    
    setupEventListeners() {
        // Track page views
        document.addEventListener('DOMContentLoaded', () => {
            this.trackPageView();
        });
        
        // Track add to cart events
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="add-to-cart"]') || 
                e.target.closest('[data-action="add-to-cart"]')) {
                this.trackAddToCart(e);
            }
        });
        
        // Track form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.contact-form') || 
                e.target.matches('.newsletter-form')) {
                this.trackFormSubmission(e);
            }
        });
    }
    
    // Location Data Management
    async loadLocationData() {
        try {
            console.log('Django Integration: Loading location data...');
            
            // Load countries with states and cities
            const countriesData = await this.makeRequest('/locations/countries/');
            if (countriesData) {
                this.countries = countriesData;
                console.log(`Loaded ${this.countries.length} countries`);
            }
            
            // Load phone codes
            const phoneCodesData = await this.makeRequest('/locations/phone_codes/');
            if (phoneCodesData) {
                this.phoneCodes = phoneCodesData;
                console.log(`Loaded ${this.phoneCodes.length} phone codes`);
            }
            
            // Populate country dropdowns on the page
            this.populateCountryDropdowns();
            
        } catch (error) {
            console.error('Error loading location data:', error);
        }
    }
    
    populateCountryDropdowns() {
        const countryDropdowns = document.querySelectorAll('select[name="country"], select[name="address[country]"]');
        const phoneCodeDropdowns = document.querySelectorAll('select[name="phone_country_code"], select[name="country_code"]');
        
        countryDropdowns.forEach(dropdown => {
            // Clear existing options except the default
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
            
            // Add change event listener to update phone code
            dropdown.addEventListener('change', (e) => {
                this.updatePhoneCode(e.target);
            });
        });
        
        // Populate phone code dropdowns
        phoneCodeDropdowns.forEach(dropdown => {
            // Clear existing options except the default
            while (dropdown.options.length > 1) {
                dropdown.remove(1);
            }
            
            // Add phone codes from API
            this.countries.forEach(country => {
                const option = document.createElement('option');
                option.value = `+${country.phone_code}`;
                option.textContent = `${country.flag_emoji} +${country.phone_code}`;
                option.dataset.countryId = country.id;
                dropdown.appendChild(option);
            });
            
            // Add change event listener to update country dropdown
            dropdown.addEventListener('change', (e) => {
                this.updateCountryFromPhoneCode(e.target);
            });
        });
    }
    
    updatePhoneCode(countryDropdown) {
        const selectedOption = countryDropdown.options[countryDropdown.selectedIndex];
        const phoneCode = selectedOption.dataset.phoneCode;
        
        // Find phone code dropdowns and update them
        const phoneCodeDropdowns = document.querySelectorAll('select[name="phone_country_code"], select[name="country_code"]');
        
        phoneCodeDropdowns.forEach(dropdown => {
            // Set the selected phone code
            for (let i = 0; i < dropdown.options.length; i++) {
                if (dropdown.options[i].value === `+${phoneCode}`) {
                    dropdown.selectedIndex = i;
                    break;
                }
            }
        });
        
        // Also update phone input fields with the country code
        const phoneInputs = document.querySelectorAll('input[name="phone"], input[name="address[phone]"]');
        
        phoneInputs.forEach(input => {
            const currentValue = input.value;
            
            // If phone number doesn't start with +, prepend the country code
            if (currentValue && !currentValue.startsWith('+')) {
                input.value = `+${phoneCode} ${currentValue}`;
            } else if (!currentValue) {
                input.value = `+${phoneCode} `;
            }
        });
        
        // Update state dropdown based on selected country
        this.updateStateDropdown(countryDropdown.value);
    }
    
    async updateStateDropdown(countryId) {
        const stateDropdowns = document.querySelectorAll('select[name="province"], select[name="address[province]"]');
        
        if (!countryId) return;
        
        try {
            const statesData = await this.makeRequest(`/locations/countries/${countryId}/states/`);
            
            stateDropdowns.forEach(dropdown => {
                // Clear existing options except the default
                while (dropdown.options.length > 1) {
                    dropdown.remove(1);
                }
                
                // Add states from API
                if (statesData) {
                    statesData.forEach(state => {
                        const option = document.createElement('option');
                        option.value = state.id;
                        option.textContent = state.name;
                        option.dataset.stateCode = state.state_code;
                        dropdown.appendChild(option);
                    });
                }
                
                // Add change event listener to update city dropdown
                dropdown.addEventListener('change', (e) => {
                    this.updateCityDropdown(e.target.value);
                });
            });
            
        } catch (error) {
            console.error('Error loading states:', error);
        }
    }
    
    updateCountryFromPhoneCode(phoneCodeDropdown) {
        const selectedOption = phoneCodeDropdown.options[phoneCodeDropdown.selectedIndex];
        const countryId = selectedOption.dataset.countryId;
        
        if (!countryId) return;
        
        // Find country dropdowns and update them
        const countryDropdowns = document.querySelectorAll('select[name="country"], select[name="address[country]"]');
        
        countryDropdowns.forEach(dropdown => {
            // Set the selected country
            for (let i = 0; i < dropdown.options.length; i++) {
                if (dropdown.options[i].value === countryId) {
                    dropdown.selectedIndex = i;
                    break;
                }
            }
            
            // Trigger the country change event to update state dropdown
            this.updateStateDropdown(countryId);
        });
    }
    async updateCityDropdown(stateId) {
        const cityDropdowns = document.querySelectorAll('select[name="city"], select[name="address[city]"]');
        
        if (!stateId) return;
        
        try {
            const citiesData = await this.makeRequest(`/locations/states/${stateId}/cities/`);
            
            cityDropdowns.forEach(dropdown => {
                // Clear existing options except the default
                while (dropdown.options.length > 1) {
                    dropdown.remove(1);
                }
                
                // Add cities from API
                if (citiesData) {
                    citiesData.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city.id;
                        option.textContent = city.name;
                        dropdown.appendChild(option);
                    });
                }
            });
            
        } catch (error) {
            console.error('Error loading cities:', error);
        }
    }
    
    async makeRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Include cookies for authentication
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Django Integration API Error:', error);
            return null;
        }
    }
    
    async trackCustomer(customer) {
        if (!customer || !customer.id) return;
        
        const customerData = {
            shopify_id: `gid://shopify/Customer/${customer.id}`,
            email: customer.email,
            first_name: customer.first_name,
            last_name: customer.last_name,
            phone: customer.phone,
            tags: customer.tags || [],
            accepts_marketing: customer.accepts_marketing,
            created_at: customer.created_at,
            updated_at: customer.updated_at,
        };
        
        // Send customer data to Django backend
        const result = await this.makeRequest('/customers/sync/', 'POST', {
            customer: customerData,
            source: 'theme_tracking'
        });
        
        if (result) {
            console.log('Customer data synced with Django backend');
        }
    }
    
    trackPageView() {
        const pageData = {
            url: window.location.href,
            path: window.location.pathname,
            title: document.title,
            referrer: document.referrer,
            timestamp: new Date().toISOString(),
            customer_id: window.Shopify?.customer?.id || null,
        };
        
        // Send page view data
        this.makeRequest('/analytics/page-view/', 'POST', pageData);
    }
    
    trackAddToCart(event) {
        // Extract product information from the event
        const productElement = event.target.closest('[data-product-id]');
        if (!productElement) return;
        
        const productId = productElement.dataset.productId;
        const variantId = productElement.dataset.variantId;
        const quantity = productElement.querySelector('[name="quantity"]')?.value || 1;
        
        const cartData = {
            product_id: productId,
            variant_id: variantId,
            quantity: parseInt(quantity),
            timestamp: new Date().toISOString(),
            customer_id: window.Shopify?.customer?.id || null,
        };
        
        // Send add to cart event
        this.makeRequest('/analytics/add-to-cart/', 'POST', cartData);
    }
    
    trackFormSubmission(event) {
        const form = event.target;
        const formData = new FormData(form);
        const formType = form.classList.contains('newsletter-form') ? 'newsletter' : 'contact';
        
        const submissionData = {
            form_type: formType,
            email: formData.get('email'),
            name: formData.get('name') || `${formData.get('first_name')} ${formData.get('last_name')}`.trim(),
            message: formData.get('message') || formData.get('body'),
            timestamp: new Date().toISOString(),
            customer_id: window.Shopify?.customer?.id || null,
        };
        
        // Send form submission data
        this.makeRequest('/analytics/form-submission/', 'POST', submissionData);
    }
    
    // Method to sync cart data with Django
    async syncCart() {
        if (!window.Shopify?.cart) return;
        
        const cartData = {
            items: window.Shopify.cart.items,
            total_price: window.Shopify.cart.total_price,
            item_count: window.Shopify.cart.item_count,
            customer_id: window.Shopify?.customer?.id || null,
            timestamp: new Date().toISOString(),
        };
        
        return await this.makeRequest('/analytics/cart-sync/', 'POST', cartData);
    }
    
    // Method to get customer recommendations from Django
    async getCustomerRecommendations(customerId) {
        if (!customerId) return null;
        
        return await this.makeRequest(`/customers/${customerId}/recommendations/`);
    }
    
    // Method to get personalized content
    async getPersonalizedContent(customerId) {
        if (!customerId) return null;
        
        return await this.makeRequest(`/customers/${customerId}/personalized-content/`);
    }
    
    // Method to update customer preferences
    async updateCustomerPreferences(customerId, preferences) {
        if (!customerId || !preferences) return null;
        
        return await this.makeRequest(`/customers/${customerId}/preferences/`, 'PUT', preferences);
    }
}

// Initialize Django Integration when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if not already done
    if (!window.djangoIntegration) {
        window.djangoIntegration = new DjangoIntegration();
    }
});

// Export for use in other scripts
window.DjangoIntegration = DjangoIntegration;
