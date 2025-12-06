"""
Bidirectional Customer Address Sync Service  
Handles Django ↔ Shopify customer address synchronization

Supports:
- Updating addresses in Django → Push to Shopify
- Importing addresses from Shopify → Save in Django
- Real-time sync with signals
- Error handling and retry logic
"""

import logging
from typing import Dict, Optional
from django.utils import timezone
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('customers.bidirectional_sync')


class CustomerAddressBidirectionalSync:
    """Service for syncing customer addresses between Django and Shopify"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def push_address_to_shopify(self, address) -> Dict:
        """
        Push customer address changes from Django to Shopify
        
        Args:
            address: ShopifyCustomerAddress instance
            
        Returns:
            Dict with success status and details
        """
        from customers.models import ShopifyCustomerAddress
        
        if not address.customer.shopify_id:
            return {
                "success": False,
                "message": "Customer has no Shopify ID",
                "address_id": address.id
            }
        
        # Determine if this is create or update
        is_update = bool(address.shopify_id and not address.shopify_id.startswith('temp_'))
        
        if is_update:
            return self._update_address_in_shopify(address)
        else:
            return self._create_address_in_shopify(address)
    
    def _create_address_in_shopify(self, address) -> Dict:
        """Create a new address in Shopify"""
        
        mutation = """
        mutation customerAddressCreate($customerId: ID!, $address: MailingAddressInput!) {
          customerAddressCreate(customerId: $customerId, address: $address) {
            customerAddress {
              id
              address1
              address2
              city
              province
              country
              zip
              phone
            }
            customerUserErrors {
              code
              field
              message
            }
          }
        }
        """
        
        variables = {
            "customerId": address.customer.shopify_id,
            "address": {
                "address1": address.address1 or "",
                "address2": address.address2 or "",
                "city": address.city or "",
                "company": address.company or "",
                "country": address.country or "",
                "firstName": address.first_name or "",
                "lastName": address.last_name or "",
                "phone": address.phone or "",
                "province": address.province or "",
                "zip": address.zip_code or ""
            }
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                error_msg = str(result["errors"])
                logger.error(f"Address creation failed: {error_msg}")
                address.shopify_push_error = error_msg
                address.save(update_fields=['shopify_push_error'])
                
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred",
                    "address_id": address.id
                }
            
            data = result.get("data", {}).get("customerAddressCreate", {})
            user_errors = data.get("customerUserErrors", [])
            
            if user_errors:
                error_msg = "; ".join([f"{e.get('field')}: {e.get('message')}" for e in user_errors])
                logger.error(f"Address validation errors: {error_msg}")
                address.shopify_push_error = error_msg
                address.save(update_fields=['shopify_push_error'])
                
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": error_msg,
                    "address_id": address.id
                }
            
            customer_address = data.get("customerAddress", {})
            
            if customer_address and customer_address.get('id'):
                # Success! Update the record with real Shopify ID
                address.shopify_id = customer_address['id']
                address.needs_shopify_push = False
                address.shopify_push_error = ""
                address.last_pushed_to_shopify = timezone.now()
                address.save(update_fields=['shopify_id', 'needs_shopify_push', 'shopify_push_error', 'last_pushed_to_shopify'])
                
                logger.info(f"✅ Created address in Shopify: {address.customer.email} - {address.city}")
                
                # If this is the default address, set it as default in Shopify
                if address.is_default:
                    self._set_default_address(address)
                
                return {
                    "success": True,
                    "message": "Address successfully created in Shopify",
                    "address_id": address.id,
                    "shopify_id": customer_address['id']
                }
            else:
                return {
                    "success": False,
                    "message": "No address returned from Shopify",
                    "address_id": address.id
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Address creation exception: {error_msg}")
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            
            return {
                "success": False,
                "message": f"Exception during creation: {error_msg}",
                "address_id": address.id
            }
    
    def _update_address_in_shopify(self, address) -> Dict:
        """Update an existing address in Shopify"""
        
        mutation = """
        mutation customerAddressUpdate($addressId: ID!, $address: MailingAddressInput!) {
          customerAddressUpdate(id: $addressId, address: $address) {
            customerAddress {
              id
              address1
              address2
              city
              province
              country
              zip
              phone
            }
            customerUserErrors {
              code
              field
              message
            }
          }
        }
        """
        
        variables = {
            "addressId": address.shopify_id,
            "address": {
                "address1": address.address1 or "",
                "address2": address.address2 or "",
                "city": address.city or "",
                "company": address.company or "",
                "country": address.country or "",
                "firstName": address.first_name or "",
                "lastName": address.last_name or "",
                "phone": address.phone or "",
                "province": address.province or "",
                "zip": address.zip_code or ""
            }
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                error_msg = str(result["errors"])
                logger.error(f"Address update failed: {error_msg}")
                address.shopify_push_error = error_msg
                address.save(update_fields=['shopify_push_error'])
                
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred",
                    "address_id": address.id
                }
            
            data = result.get("data", {}).get("customerAddressUpdate", {})
            user_errors = data.get("customerUserErrors", [])
            
            if user_errors:
                error_msg = "; ".join([f"{e.get('field')}: {e.get('message')}" for e in user_errors])
                logger.error(f"Address validation errors: {error_msg}")
                address.shopify_push_error = error_msg
                address.save(update_fields=['shopify_push_error'])
                
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": error_msg,
                    "address_id": address.id
                }
            
            customer_address = data.get("customerAddress", {})
            
            if customer_address:
                # Success!
                address.needs_shopify_push = False
                address.shopify_push_error = ""
                address.last_pushed_to_shopify = timezone.now()
                address.save(update_fields=['needs_shopify_push', 'shopify_push_error', 'last_pushed_to_shopify'])
                
                logger.info(f"✅ Updated address in Shopify: {address.customer.email} - {address.city}")
                
                # If this is the default address, set it as default in Shopify
                if address.is_default:
                    self._set_default_address(address)
                
                return {
                    "success": True,
                    "message": "Address successfully updated in Shopify",
                    "address_id": address.id
                }
            else:
                return {
                    "success": False,
                    "message": "No address returned from Shopify",
                    "address_id": address.id
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Address update exception: {error_msg}")
            address.shopify_push_error = error_msg
            address.save(update_fields=['shopify_push_error'])
            
            return {
                "success": False,
                "message": f"Exception during update: {error_msg}",
                "address_id": address.id
            }
    
    def _set_default_address(self, address) -> bool:
        """Set an address as the default address in Shopify"""
        
        mutation = """
        mutation customerDefaultAddressUpdate($customerId: ID!, $addressId: ID!) {
          customerDefaultAddressUpdate(customerId: $customerId, addressId: $addressId) {
            customer {
              id
              defaultAddress {
                id
              }
            }
            customerUserErrors {
              code
              field
              message
            }
          }
        }
        """
        
        variables = {
            "customerId": address.customer.shopify_id,
            "addressId": address.shopify_id
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" not in result:
                data = result.get("data", {}).get("customerDefaultAddressUpdate", {})
                if not data.get("customerUserErrors"):
                    logger.info(f"✅ Set default address in Shopify for {address.customer.email}")
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Failed to set default address: {e}")
            return False
    
    def push_all_pending_addresses(self) -> Dict:
        """
        Push all addresses that need Shopify sync
        
        Returns:
            Dict with statistics about the operation
        """
        from customers.models import ShopifyCustomerAddress
        
        pending_addresses = ShopifyCustomerAddress.objects.filter(
            needs_shopify_push=True
        ).select_related('customer')
        
        total = pending_addresses.count()
        success_count = 0
        error_count = 0
        errors = []
        
        logger.info(f"🔄 Starting push of {total} pending addresses...")
        
        for address in pending_addresses:
            result = self.push_address_to_shopify(address)
            
            if result["success"]:
                success_count += 1
            else:
                error_count += 1
                errors.append({
                    "address_id": address.id,
                    "customer_email": address.customer.email,
                    "city": address.city,
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"✅ Address push completed: {success_count} success, {error_count} errors out of {total} total")
        
        return {
            "success": error_count == 0,
            "total": total,
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }


# Convenience functions
def push_address_to_shopify(address) -> Dict:
    """Push a single address to Shopify"""
    service = CustomerAddressBidirectionalSync()
    return service.push_address_to_shopify(address)


def push_all_pending_addresses() -> Dict:
    """Push all pending addresses to Shopify"""
    service = CustomerAddressBidirectionalSync()
    return service.push_all_pending_addresses()
