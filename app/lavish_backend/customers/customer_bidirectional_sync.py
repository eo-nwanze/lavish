"""
Customer Bidirectional Sync Service
Handles Django → Shopify customer synchronization using GraphQL Admin API
"""

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('customers')


class CustomerBidirectionalSync:
    """Service for syncing customers from Django to Shopify"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def push_customer_to_shopify(self, customer) -> Dict:
        """
        Push a Django customer to Shopify
        
        Args:
            customer: ShopifyCustomer instance
            
        Returns:
            Dict with success status and details
        """
        from customers.models import ShopifyCustomer
        
        # Check if customer has valid Shopify ID
        has_valid_id = (customer.shopify_id and 
                       customer.shopify_id.startswith('gid://shopify/Customer/') and
                       not customer.shopify_id.startswith('gid://shopify/Customer/test'))
        
        # If has temp/test ID, treat as new customer
        if (customer.shopify_id and 
            (customer.shopify_id.startswith('test_') or 
             customer.shopify_id.startswith('temp_') or
             customer.shopify_id.startswith('gid://shopify/Customer/test'))):
            logger.info(f"Customer {customer.id} has test/temp ID, will create in Shopify")
            return self._create_new_customer(customer)
        
        # Check if this is a new customer or update
        if has_valid_id:
            # Customer exists in Shopify, update it
            return self._update_existing_customer(customer)
        else:
            # New customer, create in Shopify
            return self._create_new_customer(customer)
    
    def _create_new_customer(self, customer) -> Dict:
        """Create a new customer in Shopify using customerCreate mutation"""
        
        mutation = """
        mutation customerCreate($input: CustomerInput!) {
          customerCreate(input: $input) {
            customer {
              id
              email
              firstName
              lastName
              phone
              state
              verifiedEmail
              taxExempt
              tags
              numberOfOrders
              createdAt
              updatedAt
              addresses {
                id
                firstName
                lastName
                address1
                address2
                city
                province
                country
                zip
                phone
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        # Build customer input
        customer_input = {
            "email": customer.email,
            "firstName": customer.first_name or "",
            "lastName": customer.last_name or "",
            "phone": customer.phone or "",
            "tags": customer.tags if isinstance(customer.tags, list) else [],
        }
        
        # Add email marketing consent if customer accepts marketing
        if customer.accepts_marketing:
            customer_input["emailMarketingConsent"] = {
                "marketingState": "SUBSCRIBED",
                "marketingOptInLevel": (customer.marketing_opt_in_level.upper() 
                                       if customer.marketing_opt_in_level 
                                       else "SINGLE_OPT_IN")
            }
        
        variables = {"input": customer_input}
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                error_msg = str(result["errors"])
                logger.error(f"Customer creation failed: {error_msg}")
                customer.shopify_push_error = error_msg
                customer.save(update_fields=['shopify_push_error'])
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred",
                    "customer_id": customer.id
                }
            
            data = result.get("data", {}).get("customerCreate", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                error_msg = "; ".join([f"{e.get('field')}: {e.get('message')}" for e in user_errors])
                logger.error(f"Customer validation errors: {error_msg}")
                customer.shopify_push_error = error_msg
                customer.save(update_fields=['shopify_push_error'])
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": error_msg,
                    "customer_id": customer.id
                }
            
            # Success - update customer with Shopify ID
            shopify_customer = data.get("customer", {})
            shopify_id = shopify_customer.get("id", "")
            
            with transaction.atomic():
                customer.shopify_id = shopify_id
                customer.needs_shopify_push = False
                customer.shopify_push_error = ""
                customer.last_pushed_to_shopify = timezone.now()
                customer.save(update_fields=['shopify_id', 'needs_shopify_push', 
                                            'shopify_push_error', 'last_pushed_to_shopify'])
            
            logger.info(f"Successfully created customer {customer.id} in Shopify: {shopify_id}")
            return {
                "success": True,
                "shopify_id": shopify_id,
                "message": f"Customer '{customer.email}' created in Shopify",
                "customer_id": customer.id
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception creating customer {customer.id}: {error_msg}")
            customer.shopify_push_error = error_msg
            customer.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "customer_id": customer.id
            }
    
    def _update_existing_customer(self, customer) -> Dict:
        """Update an existing customer in Shopify using customerUpdate mutation"""
        
        mutation = """
        mutation customerUpdate($input: CustomerInput!) {
          customerUpdate(input: $input) {
            customer {
              id
              email
              firstName
              lastName
              phone
              state
              tags
              acceptsMarketing
              updatedAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        # Build customer input
        customer_input = {
            "id": customer.shopify_id,
            "email": customer.email,
            "firstName": customer.first_name or "",
            "lastName": customer.last_name or "",
            "phone": customer.phone or "",
            "tags": customer.tags if isinstance(customer.tags, list) else [],
        }
        
        variables = {"input": customer_input}
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                error_msg = str(result["errors"])
                logger.error(f"Customer update failed: {error_msg}")
                customer.shopify_push_error = error_msg
                customer.save(update_fields=['shopify_push_error'])
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred",
                    "customer_id": customer.id
                }
            
            data = result.get("data", {}).get("customerUpdate", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                error_msg = "; ".join([f"{e.get('field')}: {e.get('message')}" for e in user_errors])
                logger.error(f"Customer update validation errors: {error_msg}")
                customer.shopify_push_error = error_msg
                customer.save(update_fields=['shopify_push_error'])
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": error_msg,
                    "customer_id": customer.id
                }
            
            # Success
            with transaction.atomic():
                customer.needs_shopify_push = False
                customer.shopify_push_error = ""
                customer.last_pushed_to_shopify = timezone.now()
                customer.save(update_fields=['needs_shopify_push', 'shopify_push_error', 
                                            'last_pushed_to_shopify'])
            
            logger.info(f"Successfully updated customer {customer.id} in Shopify")
            return {
                "success": True,
                "message": f"Customer '{customer.email}' updated in Shopify",
                "customer_id": customer.id
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception updating customer {customer.id}: {error_msg}")
            customer.shopify_push_error = error_msg
            customer.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "customer_id": customer.id
            }
    
    def push_all_pending_customers(self) -> Dict:
        """
        Push all customers that need syncing to Shopify
        
        Returns:
            Dict with statistics
        """
        from customers.models import ShopifyCustomer
        
        pending_customers = ShopifyCustomer.objects.filter(needs_shopify_push=True)
        
        results = {
            "total": pending_customers.count(),
            "success_count": 0,
            "error_count": 0,
            "errors": []
        }
        
        for customer in pending_customers:
            result = self.push_customer_to_shopify(customer)
            
            if result.get("success"):
                results["success_count"] += 1
            else:
                results["error_count"] += 1
                results["errors"].append({
                    "customer_id": customer.id,
                    "email": customer.email,
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"Pushed {results['success_count']}/{results['total']} customers to Shopify")
        return results


# Convenience functions for easy import
def push_customer_to_shopify(customer):
    """Push a single customer to Shopify"""
    sync_service = CustomerBidirectionalSync()
    return sync_service.push_customer_to_shopify(customer)


def push_all_pending_customers():
    """Push all pending customers to Shopify"""
    sync_service = CustomerBidirectionalSync()
    return sync_service.push_all_pending_customers()
