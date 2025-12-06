"""
Customer Address Bidirectional Sync Service (FIXED)
Handles Django → Shopify customer address synchronization using proper GraphQL Admin API
Based on Shopify Admin API 2024-10 specification
"""

import logging
from typing import Dict
from django.utils import timezone
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('customers')


class CustomerAddressBidirectionalSyncFixed:
    """Service for syncing customer addresses from Django to Shopify with proper mutations"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def push_address_to_shopify(self, address) -> Dict:
        """
        Push a Django customer address to Shopify
        
        Args:
            address: ShopifyCustomerAddress instance
            
        Returns:
            Dict with success status and details
        """
        from customers.models import ShopifyCustomerAddress
        
        # Validate customer has real Shopify ID
        if not address.customer.shopify_id:
            return {
                "success": False,
                "message": "Customer has no Shopify ID",
                "address_id": address.id
            }
        
        # Skip test/temp customer IDs
        if (address.customer.shopify_id.startswith('test_') or 
            address.customer.shopify_id.startswith('temp_')):
            error_msg = f"Cannot push address for customer with test/temp ID: {address.customer.shopify_id}"
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "address_id": address.id
            }
        
        # Check if address is new or existing
        if address.shopify_id and not address.shopify_id.startswith('temp_'):
            # Existing address - update it
            return self._update_address_in_shopify(address)
        else:
            # New address - create it
            return self._create_address_in_shopify(address)
    
    def _create_address_in_shopify(self, address) -> Dict:
        """
        Create a new address in Shopify
        Using REST API since GraphQL customerAddressCreate has been deprecated
        """
        
        # Extract customer numeric ID from Shopify GID
        customer_id = address.customer.shopify_id.split('/')[-1]
        
        # Prepare address data for REST API
        address_data = {
            "address": {
                "first_name": address.first_name or "",
                "last_name": address.last_name or "",
                "company": address.company or "",
                "address1": address.address1 or "",
                "address2": address.address2 or "",
                "city": address.city or "",
                "province": address.province or "",
                "country": address.country or "",
                "zip": address.zip_code or "",
                "phone": address.phone or "",
            }
        }
        
        # Use REST API endpoint for customer address creation
        import requests
        
        api_version = self.client.api_version
        base_url = f"https://{self.client.shop_domain}/admin/api/{api_version}"
        url = f"{base_url}/customers/{customer_id}/addresses.json"
        
        headers = {
            "X-Shopify-Access-Token": self.client.access_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=address_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                created_address = result.get("customer_address", {})
                
                if created_address and created_address.get('id'):
                    # Convert REST ID to GraphQL GID format
                    shopify_id = f"gid://shopify/MailingAddress/{created_address['id']}?model_name=CustomerAddress"
                    
                    address.shopify_id = shopify_id
                    address.needs_shopify_push = False
                    address.shopify_push_error = ""
                    address.last_pushed_to_shopify = timezone.now()
                    address.save(update_fields=['shopify_id', 'needs_shopify_push', 
                                                'shopify_push_error', 'last_pushed_to_shopify'])
                    
                    logger.info(f"✅ Created address in Shopify: {address.customer.email} - {address.city}")
                    
                    # Set as default if needed
                    if address.is_default:
                        self._set_default_address_rest(customer_id, created_address['id'])
                    
                    return {
                        "success": True,
                        "message": "Address successfully created in Shopify",
                        "address_id": address.id,
                        "shopify_id": shopify_id
                    }
            
            # Handle errors
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Address creation failed: {error_msg}")
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            
            return {
                "success": False,
                "message": error_msg,
                "address_id": address.id
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception creating address {address.id}: {error_msg}")
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "address_id": address.id
            }
    
    def _update_address_in_shopify(self, address) -> Dict:
        """Update an existing address in Shopify using REST API"""
        
        # Extract IDs from GIDs
        customer_id = address.customer.shopify_id.split('/')[-1]
        
        # Extract address ID (handle different formats)
        if 'MailingAddress/' in address.shopify_id:
            address_id = address.shopify_id.split('MailingAddress/')[1].split('?')[0]
        else:
            address_id = address.shopify_id.split('/')[-1].split('?')[0]
        
        # Prepare address data
        address_data = {
            "address": {
                "id": int(address_id),
                "first_name": address.first_name or "",
                "last_name": address.last_name or "",
                "company": address.company or "",
                "address1": address.address1 or "",
                "address2": address.address2 or "",
                "city": address.city or "",
                "province": address.province or "",
                "country": address.country or "",
                "zip": address.zip_code or "",
                "phone": address.phone or "",
            }
        }
        
        # Use REST API endpoint for customer address update
        import requests
        
        api_version = self.client.api_version
        base_url = f"https://{self.client.shop_domain}/admin/api/{api_version}"
        url = f"{base_url}/customers/{customer_id}/addresses/{address_id}.json"
        
        headers = {
            "X-Shopify-Access-Token": self.client.access_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.put(url, json=address_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                address.needs_shopify_push = False
                address.shopify_push_error = ""
                address.last_pushed_to_shopify = timezone.now()
                address.save(update_fields=['needs_shopify_push', 'shopify_push_error', 
                                            'last_pushed_to_shopify'])
                
                logger.info(f"✅ Updated address in Shopify: {address.customer.email} - {address.city}")
                
                # Set as default if needed
                if address.is_default:
                    self._set_default_address_rest(customer_id, address_id)
                
                return {
                    "success": True,
                    "message": "Address successfully updated in Shopify",
                    "address_id": address.id
                }
            
            # Handle errors
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Address update failed: {error_msg}")
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            
            return {
                "success": False,
                "message": error_msg,
                "address_id": address.id
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception updating address {address.id}: {error_msg}")
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            return {
                "success": False,
                "message": error_msg,
                "address_id": address.id
            }
    
    def _set_default_address_rest(self, customer_id, address_id):
        """Set an address as default using REST API"""
        import requests
        
        api_version = self.client.api_version
        base_url = f"https://{self.client.shop_domain}/admin/api/{api_version}"
        url = f"{base_url}/customers/{customer_id}/addresses/{address_id}/default.json"
        
        headers = {
            "X-Shopify-Access-Token": self.client.access_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.put(url, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Set address {address_id} as default for customer {customer_id}")
                return True
            else:
                logger.warning(f"Failed to set default address: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception setting default address: {e}")
            return False
    
    def push_all_pending_addresses(self) -> Dict:
        """
        Push all addresses that need syncing to Shopify
        
        Returns:
            Dict with statistics
        """
        from customers.models import ShopifyCustomerAddress
        
        pending_addresses = ShopifyCustomerAddress.objects.filter(needs_shopify_push=True)
        
        results = {
            "total": pending_addresses.count(),
            "success_count": 0,
            "error_count": 0,
            "errors": []
        }
        
        for address in pending_addresses:
            result = self.push_address_to_shopify(address)
            
            if result.get("success"):
                results["success_count"] += 1
            else:
                results["error_count"] += 1
                results["errors"].append({
                    "address_id": address.id,
                    "customer": address.customer.email,
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"Pushed {results['success_count']}/{results['total']} addresses to Shopify")
        return results


# Convenience functions for easy import
def push_address_to_shopify(address):
    """Push a single address to Shopify"""
    sync_service = CustomerAddressBidirectionalSyncFixed()
    return sync_service.push_address_to_shopify(address)


def push_all_pending_addresses():
    """Push all pending addresses to Shopify"""
    sync_service = CustomerAddressBidirectionalSyncFixed()
    return sync_service.push_all_pending_addresses()
