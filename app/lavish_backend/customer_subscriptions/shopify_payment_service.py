"""
Shopify Payment Method Service
Handles integration with Shopify's Customer Payment Methods API
Allows Django backend to leverage Shopify's saved payment methods for subscriptions
"""

import shopify
from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ShopifyPaymentMethodService:
    """
    Service for managing customer payment methods through Shopify API
    Enables subscription payments using Shopify's saved payment methods
    """
    
    def __init__(self, shop_domain=None, access_token=None):
        """Initialize Shopify session"""
        self.shop_domain = shop_domain or settings.SHOPIFY_STORE_URL
        self.access_token = access_token or settings.SHOPIFY_ACCESS_TOKEN
        
        # Initialize Shopify session
        self.session = shopify.Session(self.shop_domain, settings.SHOPIFY_API_VERSION, self.access_token)
        shopify.ShopifyResource.activate_session(self.session)
    
    def get_customer_payment_methods(self, customer_id):
        """
        Get all saved payment methods for a customer
        
        Args:
            customer_id (int or str): Customer ID (can be numeric or GID)
        
        Returns:
            dict: Payment methods data including cards, tokens, etc.
        """
        # Ensure customer_id is in GID format
        if not str(customer_id).startswith('gid://'):
            customer_id = f"gid://shopify/Customer/{customer_id}"
        
        query = """
        query GetCustomerPaymentMethods($customerId: ID!) {
            customer(id: $customerId) {
                id
                displayName
                email
                paymentMethods(first: 10) {
                    edges {
                        node {
                            id
                            instrument
                            ... on CustomerCreditCard {
                                brand
                                lastDigits
                                expiryMonth
                                expiryYear
                                maskedNumber
                            }
                            ... on CustomerPaypalBillingAgreement {
                                billingAddress {
                                    address1
                                    city
                                    province
                                    country
                                    zip
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {"customerId": customer_id}
        
        try:
            result = shopify.GraphQL().execute(query, variables)
            data = result if isinstance(result, dict) else eval(result)
            
            if 'errors' in data:
                logger.error(f"Error fetching payment methods: {data['errors']}")
                return None
            
            return data.get('data', {}).get('customer')
        
        except Exception as e:
            logger.error(f"Exception getting payment methods: {str(e)}")
            return None
    
    def get_default_payment_method(self, customer_id):
        """
        Get the customer's default/primary payment method
        
        Args:
            customer_id: Customer ID
        
        Returns:
            dict: Default payment method details or None
        """
        customer_data = self.get_customer_payment_methods(customer_id)
        
        if not customer_data:
            return None
        
        payment_methods = customer_data.get('paymentMethods', {}).get('edges', [])
        
        # Return first payment method as default
        if payment_methods:
            return payment_methods[0]['node']
        
        return None
    
    def create_subscription_contract_with_payment(
        self, 
        customer_id, 
        payment_method_id, 
        selling_plan_details,
        delivery_address=None
    ):
        """
        Create a subscription contract using a saved payment method
        
        Args:
            customer_id: Shopify customer ID
            payment_method_id: Shopify payment method ID
            selling_plan_details: Dict with plan configuration
            delivery_address: Optional delivery address override
        
        Returns:
            dict: Subscription contract creation result
        """
        # Ensure IDs are in GID format
        if not str(customer_id).startswith('gid://'):
            customer_id = f"gid://shopify/Customer/{customer_id}"
        
        mutation = """
        mutation CreateSubscriptionContract($input: SubscriptionContractCreateInput!) {
            subscriptionContractCreate(input: $input) {
                subscriptionContract {
                    id
                    status
                    nextBillingDate
                    billingPolicy {
                        interval
                        intervalCount
                    }
                    deliveryPolicy {
                        interval
                        intervalCount
                    }
                    lines(first: 10) {
                        edges {
                            node {
                                id
                                productId
                                quantity
                                currentPrice {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        # Build line items
        lines = []
        for item in selling_plan_details.get('line_items', []):
            line = {
                "productVariantId": item['variant_id'],
                "quantity": item.get('quantity', 1),
                "currentPrice": str(item['price'])
            }
            
            # Add selling plan if provided
            if item.get('selling_plan_id'):
                line['sellingPlanId'] = item['selling_plan_id']
            
            lines.append(line)
        
        # Build input
        input_data = {
            "customerId": customer_id,
            "paymentMethodId": payment_method_id,
            "currencyCode": selling_plan_details.get('currency', 'USD'),
            "billingPolicy": {
                "interval": selling_plan_details['billing_interval'].upper(),
                "intervalCount": selling_plan_details['billing_interval_count']
            },
            "deliveryPolicy": {
                "interval": selling_plan_details['delivery_interval'].upper(),
                "intervalCount": selling_plan_details['delivery_interval_count']
            },
            "lines": lines
        }
        
        # Add delivery address if provided
        if delivery_address:
            input_data['deliveryMethod'] = {
                "shipping": {
                    "address": delivery_address
                }
            }
        
        # Add billing date if specified
        if selling_plan_details.get('next_billing_date'):
            input_data['nextBillingDate'] = selling_plan_details['next_billing_date']
        
        variables = {"input": input_data}
        
        try:
            result = shopify.GraphQL().execute(mutation, variables)
            data = result if isinstance(result, dict) else eval(result)
            
            if 'errors' in data:
                logger.error(f"Error creating subscription: {data['errors']}")
                return {'success': False, 'errors': data['errors']}
            
            contract_data = data.get('data', {}).get('subscriptionContractCreate', {})
            
            if contract_data.get('userErrors'):
                logger.error(f"User errors: {contract_data['userErrors']}")
                return {'success': False, 'errors': contract_data['userErrors']}
            
            return {
                'success': True,
                'contract': contract_data.get('subscriptionContract')
            }
        
        except Exception as e:
            logger.error(f"Exception creating subscription: {str(e)}")
            return {'success': False, 'errors': [{'message': str(e)}]}
    
    def update_subscription_payment_method(self, subscription_contract_id, new_payment_method_id):
        """
        Update the payment method for an existing subscription
        
        Args:
            subscription_contract_id: Subscription contract GID
            new_payment_method_id: New payment method GID
        
        Returns:
            dict: Update result
        """
        mutation = """
        mutation UpdateSubscriptionPaymentMethod($contractId: ID!, $paymentMethodId: ID!) {
            subscriptionContractUpdate(
                contractId: $contractId
                contract: {
                    paymentMethodId: $paymentMethodId
                }
            ) {
                subscriptionContract {
                    id
                    status
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {
            "contractId": subscription_contract_id,
            "paymentMethodId": new_payment_method_id
        }
        
        try:
            result = shopify.GraphQL().execute(mutation, variables)
            data = result if isinstance(result, dict) else eval(result)
            
            return data.get('data', {}).get('subscriptionContractUpdate', {})
        
        except Exception as e:
            logger.error(f"Exception updating payment method: {str(e)}")
            return {'userErrors': [{'message': str(e)}]}
    
    def verify_payment_method_active(self, payment_method_id):
        """
        Verify that a payment method is still valid and active
        
        Args:
            payment_method_id: Payment method GID
        
        Returns:
            bool: True if payment method is valid
        """
        # Extract customer ID from payment method
        # This is a simplified check - in production you'd want more validation
        query = """
        query VerifyPaymentMethod($id: ID!) {
            node(id: $id) {
                ... on CustomerPaymentMethod {
                    id
                    instrument
                }
            }
        }
        """
        
        variables = {"id": payment_method_id}
        
        try:
            result = shopify.GraphQL().execute(query, variables)
            data = result if isinstance(result, dict) else eval(result)
            
            return data.get('data', {}).get('node') is not None
        
        except Exception as e:
            logger.error(f"Exception verifying payment method: {str(e)}")
            return False
    
    def __del__(self):
        """Clean up Shopify session"""
        try:
            shopify.ShopifyResource.clear_session()
        except:
            pass
