/**
 * Subscription Checkout Integration
 * Handles subscription sign-up flow and checkout creation
 */

class SubscriptionCheckout {
    constructor() {
        this.apiBase = '/api/subscriptions';
        this.init();
    }

    init() {
        // Initialize subscription checkout functionality
        this.bindEvents();
        this.loadSubscriptionOptions();
    }

    bindEvents() {
        // Bind subscription button events
        document.addEventListener('click', (e) => {
            if (e.target.matches('.subscribe-btn')) {
                e.preventDefault();
                const planId = e.target.dataset.planId;
                const planName = e.target.dataset.planName;
                const productId = e.target.dataset.productId;
                const productHandle = e.target.dataset.productHandle;
                this.createSubscriptionCheckout(planId, planName, productId, productHandle, e.target);
            }
        });
    }

    async loadSubscriptionOptions() {
        // This is now handled in the liquid template
        // Keeping for backward compatibility
        console.log('SubscriptionCheckout initialized');
    }

    async getAvailableSellingPlans(productId) {
        const response = await fetch(`${this.apiBase}/selling-plans/?product_id=${productId}`);
        const data = await response.json();
        return data.selling_plans || [];
    }

    async createSubscriptionCheckout(planId, planName, productId, productHandle, button) {
        try {
            // Show loading state
            const originalText = button.textContent;
            button.textContent = 'Subscribing...';
            button.disabled = true;

            // Try multiple endpoints for reliability
            const endpoints = [
                'http://127.0.0.1:8003/api/subscriptions/checkout/create/',
                'http://localhost:8003/api/subscriptions/checkout/create/',
                '/api/subscriptions/checkout/create/'
            ];

            let checkoutData = null;
            let lastError = null;

            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            selling_plan_id: planId,
                            product_id: productId,
                            quantity: 1
                        })
                    });

                    if (response.ok) {
                        checkoutData = await response.json();
                        break;
                    }
                } catch (error) {
                    lastError = error;
                    continue;
                }
            }

            if (checkoutData && checkoutData.success) {
                this.showCheckoutSuccess(button, planName, checkoutData);
            } else {
                throw new Error(lastError?.message || checkoutData?.error || 'Checkout failed');
            }

        } catch (error) {
            console.error('Subscription checkout error:', error);
            this.showCheckoutError(button, error.message);
        }
    }

    showCheckoutSuccess(button, planName, data) {
        const container = button.closest('.product-subscription-options');
        const successHTML = `
            <div class="subscription-success">
                <h4>Subscription Created!</h4>
                <p>You've successfully subscribed to <strong>${planName}</strong>.</p>
                <div class="subscription-details">
                    <p><strong>Subscription ID:</strong> ${data.subscription_id || 'Processing...'}</p>
                    <p><strong>Next Billing:</strong> ${data.next_billing_date || 'Processing...'}</p>
                </div>
                <div class="subscription-actions">
                    <button class="manage-subscription-btn" onclick="window.open('/account/subscriptions', '_blank')">
                        Manage Subscription
                    </button>
                    <button class="continue-shopping-btn" onclick="location.reload()">
                        Continue Shopping
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = successHTML;
    }

    showCheckoutError(button, message) {
        // Restore button state
        button.disabled = false;
        button.textContent = 'Subscribe';
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'subscription-checkout-error';
        errorDiv.innerHTML = `
            <p>${message}</p>
            <button class="retry-btn" onclick="location.reload()">Try Again</button>
        `;
        
        button.parentNode.appendChild(errorDiv);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
}

// Initialize the subscription checkout system
window.subscriptionCheckout = new SubscriptionCheckout();

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SubscriptionCheckout;
}