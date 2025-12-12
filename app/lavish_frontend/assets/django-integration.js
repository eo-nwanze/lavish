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
            console.log('Backend URL:', this.baseUrl);
            
            // Load countries with states and cities
            const countriesData = await this.makeRequest('/locations/countries/');
            if (countriesData) {
                this.countries = countriesData;
                console.log(`✅ Loaded ${this.countries.length} countries`);
            } else {
                console.error('❌ Failed to load countries - no data returned');
                console.log('Tip: Ensure Django backend is running at:', this.baseUrl);
            }
            
            // Load phone codes
            const phoneCodesData = await this.makeRequest('/locations/phone_codes/');
            if (phoneCodesData) {
                this.phoneCodes = phoneCodesData;
                console.log(`✅ Loaded ${this.phoneCodes.length} phone codes`);
            } else {
                console.error('❌ Failed to load phone codes');
            }
            
            // Populate country dropdowns on the page
            if (this.countries.length > 0) {
                this.populateCountryDropdowns();
                console.log('✅ Country dropdowns populated');
            } else {
                console.warn('⚠️ No countries available to populate dropdowns');
            }
            
        } catch (error) {
            console.error('❌ Error loading location data:', error);
            console.log('Django backend might not be running. Start with: python manage.py runserver 8003');
        }
    }
    
    populateCountryDropdowns() {
        console.log('🌍 Attempting to populate country dropdowns...');
        
        // Find all country dropdowns including add/edit address modals
        const countryDropdowns = document.querySelectorAll('select[name="country"], select[name="address[country]"], select[id="change_addr_country"], select[id="addr_country"], select[id="edit_addr_country"]');
        const phoneCodeDropdowns = document.querySelectorAll('select[name="phone_country_code"], select[name="country_code"], select[id="change_addr_country_code"], select[id="addr_country_code"], select[id="edit_addr_country_code"]');
        
        console.log(`Found ${countryDropdowns.length} country dropdowns and ${phoneCodeDropdowns.length} phone code dropdowns`);
        
        if (countryDropdowns.length === 0) {
            console.warn('⚠️ No country dropdowns found in DOM. Will retry when modals open.');
            return;
        }
        
        let populatedCount = 0;
        
        countryDropdowns.forEach(dropdown => {
            if (!dropdown) return;
            
            // Clear existing options except the first one (placeholder)
            while (dropdown.options.length > 1) {
                dropdown.remove(1);
            }
            
            // Update placeholder text
            if (dropdown.options[0]) {
                dropdown.options[0].textContent = 'Select Country...';
            }
            
            // Add countries from API
            this.countries.forEach(country => {
                const option = document.createElement('option');
                option.value = country.id;
                option.textContent = `${country.flag_emoji} ${country.name} (+${country.phone_code})`;
                option.dataset.phoneCode = country.phone_code;
                option.dataset.countryId = country.id;
                dropdown.appendChild(option);
            });
            
            populatedCount++;
            console.log(`✅ Populated ${dropdown.id || 'unnamed'} with ${this.countries.length} countries`);
            
            // Add change event listener to update phone code (only once)
            if (!dropdown.dataset.listenerAdded) {
                dropdown.addEventListener('change', (e) => {
                    this.handleCountryChange(e.target);
                });
                dropdown.dataset.listenerAdded = 'true';
            }
        });
        
        // Populate phone code dropdowns
        phoneCodeDropdowns.forEach(dropdown => {
            if (!dropdown) return;
            
            // Clear existing options except the first one
            while (dropdown.options.length > 1) {
                dropdown.remove(1);
            }
            
            // Update placeholder text
            if (dropdown.options[0]) {
                dropdown.options[0].textContent = 'Select Code...';
            }
            
            // Add phone codes from API
            this.countries.forEach(country => {
                const option = document.createElement('option');
                option.value = `+${country.phone_code}`;
                option.textContent = `${country.flag_emoji} +${country.phone_code}`;
                option.dataset.countryId = country.id;
                dropdown.appendChild(option);
            });
            
            // Add change event listener (only once)
            if (!dropdown.dataset.listenerAdded) {
                dropdown.addEventListener('change', (e) => {
                    this.updateCountryFromPhoneCode(e.target);
                });
                dropdown.dataset.listenerAdded = 'true';
            }
        });
        
        console.log(`✅ Successfully populated ${populatedCount} country dropdowns`);
    }
    
    // New method to handle country selection
    handleCountryChange(countryDropdown) {
        const selectedOption = countryDropdown.options[countryDropdown.selectedIndex];
        const phoneCode = selectedOption.dataset.phoneCode;
        const countryId = countryDropdown.value;
        
        console.log(`Country changed to: ${selectedOption.textContent}, ID: ${countryId}`);
        
        // Update phone code dropdown
        this.updatePhoneCode(countryDropdown);
        
        // Load states for selected country
        if (countryId) {
            this.updateStateDropdown(countryId);
        }
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
        const stateDropdowns = document.querySelectorAll('select[name="province"], select[name="address[province]"], select[id="addr_province"], select[id="edit_addr_province"], select[id="change_addr_province"]');
        
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
        const cityDropdowns = document.querySelectorAll('select[name="city"], select[name="address[city]"], select[id="addr_city"], select[id="edit_addr_city"], select[id="change_addr_city"]');
        
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
            console.log(`🌐 API Request: ${method} ${url}`);
            const response = await fetch(url, options);
            
            if (!response.ok) {
                console.error(`❌ API Error: ${response.status} ${response.statusText}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const jsonData = await response.json();
            console.log(`✅ API Response received for ${endpoint}`);
            return jsonData;
        } catch (error) {
            console.error(`❌ Django Integration API Error for ${endpoint}:`, error);
            console.log('Ensure Django backend is running and CORS is configured');
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
    
    // Method to populate change address modal dropdowns
    populateChangeAddressModal() {
        console.log('Django Integration: Populating change address modal...');
        console.log('Available countries:', this.countries.length);
        
        const countrySelect = document.getElementById('change_addr_country');
        const countryCodeSelect = document.getElementById('change_addr_country_code');
        const stateSelect = document.getElementById('change_addr_province');
        const citySelect = document.getElementById('change_addr_city');
        
        console.log('Elements found:', {
            countrySelect: !!countrySelect,
            countryCodeSelect: !!countryCodeSelect,
            stateSelect: !!stateSelect,
            citySelect: !!citySelect
        });
        
        if (!countrySelect || !countryCodeSelect) {
            console.error('Change address modal elements not found');
            return;
        }
        
        // Clear existing options
        countrySelect.innerHTML = '<option value="">Select a country...</option>';
        countryCodeSelect.innerHTML = '<option value="">Select...</option>';
        
        // Add countries
        this.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.id;
            option.textContent = country.name;
            option.dataset.phoneCode = country.phone_code;
            countrySelect.appendChild(option);
            
            const codeOption = document.createElement('option');
            codeOption.value = `+${country.phone_code}`;
            codeOption.textContent = `(+${country.phone_code})`;
            countryCodeSelect.appendChild(codeOption);
        });
        
        // Add change event listener for country
        countrySelect.addEventListener('change', async (e) => {
            const countryId = e.target.value;
            if (!countryId) {
                stateSelect.innerHTML = '<option value="">Select country first</option>';
                citySelect.innerHTML = '<option value="">Select state first</option>';
                return;
            }
            
            // Update phone code
            const selectedCountry = this.countries.find(c => c.id == countryId);
            if (selectedCountry) {
                countryCodeSelect.value = `+${selectedCountry.phone_code}`;
            }
            
            // Load states
            try {
                stateSelect.innerHTML = '<option value="">Loading states...</option>';
                citySelect.innerHTML = '<option value="">Select state first...</option>';
                
                const states = await this.makeRequest(`/locations/countries/${countryId}/states/`);
                stateSelect.innerHTML = '<option value="">Select state/province...</option>';
                
                if (states.length > 0) {
                    states.forEach(state => {
                        const option = document.createElement('option');
                        option.value = state.id;
                        option.textContent = state.name;
                        stateSelect.appendChild(option);
                    });
                    
                    // Add change event listener for state
                    stateSelect.addEventListener('change', async (e) => {
                        const stateId = e.target.value;
                        if (!stateId || stateId === 'N/A') {
                            citySelect.innerHTML = '<option value="">Enter city manually...</option>';
                            return;
                        }
                        
                        // Load cities
                        try {
                            citySelect.innerHTML = '<option value="">Loading cities...</option>';
                            const cities = await this.makeRequest(`/locations/states/${stateId}/cities/`);
                            citySelect.innerHTML = '<option value="">Select city...</option>';
                            
                            cities.forEach(city => {
                                const option = document.createElement('option');
                                option.value = city.id;
                                option.textContent = city.name;
                                citySelect.appendChild(option);
                            });
                        } catch (error) {
                            console.error('Error loading cities:', error);
                            citySelect.innerHTML = '<option value="">Error loading cities</option>';
                        }
                    });
                } else {
                    stateSelect.innerHTML = '<option value="N/A">N/A</option>';
                    citySelect.innerHTML = '<option value="">Enter city manually...</option>';
                }
            } catch (error) {
                console.error('Error loading states:', error);
                stateSelect.innerHTML = '<option value="">Error loading states</option>';
            }
        });
    }
}

// Initialize Django Integration when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if not already done
    if (!window.djangoIntegration) {
        window.djangoIntegration = new DjangoIntegration();
    }
    
    // Also try to populate dropdowns after a short delay to ensure modals are ready
    setTimeout(function() {
        if (window.djangoIntegration && window.djangoIntegration.countries.length > 0) {
            console.log('🔄 Re-attempting dropdown population after delay...');
            window.djangoIntegration.populateCountryDropdowns();
        }
    }, 1000);
    
    // Listen for modal open events and populate dropdowns
    document.addEventListener('click', function(e) {
        // Check if a modal-related button was clicked
        if (e.target.closest('[onclick*="openModal"]') || 
            e.target.closest('.add-address-btn') ||
            e.target.closest('.edit-address-btn')) {
            
            setTimeout(function() {
                if (window.djangoIntegration && window.djangoIntegration.countries.length > 0) {
                    console.log('🔄 Populating dropdowns after modal open...');
                    window.djangoIntegration.populateCountryDropdowns();
                }
            }, 100);
        }
    });
});

// Export for use in other scripts
window.DjangoIntegration = DjangoIntegration;

// Global helper function to manually trigger dropdown population
window.populateLocationDropdowns = function() {
    if (window.djangoIntegration && window.djangoIntegration.countries.length > 0) {
        console.log('🔄 Manual dropdown population triggered...');
        window.djangoIntegration.populateCountryDropdowns();
    } else {
        console.warn('⚠️ Django Integration not ready or no countries loaded');
    }
};
