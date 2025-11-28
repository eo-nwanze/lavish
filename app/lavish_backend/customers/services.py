import logging
from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import ShopifyCustomer, ShopifyCustomerAddress, CustomerSyncLog
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('shopify_integration')


class CustomerSyncService:
    """Service for synchronizing customer data with Shopify"""
    
    def __init__(self, store_domain=None):
        self.client = EnhancedShopifyAPIClient(shop_domain=store_domain)
        self.store_domain = store_domain or self.client.shop_domain
    
    def sync_all_customers(self):
        """Sync all customers from Shopify"""
        sync_log = CustomerSyncLog.objects.create(
            operation_type='bulk_import',
            store_domain=self.store_domain
        )
        
        try:
            sync_log.status = 'running'
            sync_log.started_at = timezone.now()
            sync_log.save()
            
            cursor = None
            total_processed = 0
            total_created = 0
            total_updated = 0
            errors = []
            
            while True:
                logger.info(f"Fetching customers batch, cursor: {cursor}")
                response = self.client.get_customers(limit=50, cursor=cursor)
                
                if 'error' in response:
                    errors.append(response['error'])
                    break
                
                customers_data = response.get('data', {}).get('customers', {})
                customers = customers_data.get('nodes', [])
                page_info = customers_data.get('pageInfo', {})
                
                if not customers:
                    break
                
                # Process each customer
                for customer_data in customers:
                    try:
                        created = self._sync_customer(customer_data)
                        total_processed += 1
                        if created:
                            total_created += 1
                        else:
                            total_updated += 1
                    except Exception as e:
                        logger.error(f"Error syncing customer {customer_data.get('id')}: {e}")
                        errors.append(str(e))
                        sync_log.errors_count += 1
                
                # Check if there are more pages
                if not page_info.get('hasNextPage'):
                    break
                
                cursor = page_info.get('endCursor')
            
            # Update sync log
            sync_log.customers_processed = total_processed
            sync_log.customers_created = total_created
            sync_log.customers_updated = total_updated
            sync_log.completed_at = timezone.now()
            sync_log.status = 'completed' if not errors else 'failed'
            
            if errors:
                sync_log.error_details = {'errors': errors}
            
            sync_log.save()
            
            logger.info(f"Customer sync completed: {total_processed} processed, {total_created} created, {total_updated} updated")
            return sync_log
            
        except Exception as e:
            logger.error(f"Customer sync failed: {e}")
            sync_log.status = 'failed'
            sync_log.error_details = {'error': str(e)}
            sync_log.completed_at = timezone.now()
            sync_log.save()
            raise
    
    def _sync_customer(self, customer_data):
        """Sync a single customer"""
        shopify_id = customer_data['id']
        
        # Parse timestamps
        created_at = parse_datetime(customer_data['createdAt'])
        updated_at = parse_datetime(customer_data['updatedAt'])
        
        # Get or create customer
        customer, created = ShopifyCustomer.objects.get_or_create(
            shopify_id=shopify_id,
            defaults={
                'email': customer_data.get('email', ''),
                'first_name': customer_data.get('firstName', ''),
                'last_name': customer_data.get('lastName', ''),
                'phone': customer_data.get('phone', ''),
                'state': customer_data.get('state', 'ENABLED'),
                'verified_email': customer_data.get('verifiedEmail', False),
                'tax_exempt': customer_data.get('taxExempt', False),
                'number_of_orders': customer_data.get('numberOfOrders', 0),
                'tags': customer_data.get('tags', []),
                'created_at': created_at,
                'updated_at': updated_at,
                'store_domain': self.store_domain,
            }
        )
        
        if not created:
            # Update existing customer
            customer.email = customer_data.get('email', '')
            customer.first_name = customer_data.get('firstName', '')
            customer.last_name = customer_data.get('lastName', '')
            customer.phone = customer_data.get('phone', '')
            customer.state = customer_data.get('state', 'ENABLED')
            customer.verified_email = customer_data.get('verifiedEmail', False)
            customer.tax_exempt = customer_data.get('taxExempt', False)
            customer.number_of_orders = customer_data.get('numberOfOrders', 0)
            customer.tags = customer_data.get('tags', [])
            customer.updated_at = updated_at
            customer.sync_status = 'synced'
            customer.save()
        
        # Sync addresses
        addresses_data = customer_data.get('addresses', [])
        for address_data in addresses_data:
            self._sync_customer_address(customer, address_data)
        
        return created
    
    def _sync_customer_address(self, customer, address_data):
        """Sync a customer address"""
        shopify_id = address_data['id']
        
        address, created = ShopifyCustomerAddress.objects.get_or_create(
            shopify_id=shopify_id,
            defaults={
                'customer': customer,
                'first_name': address_data.get('firstName', ''),
                'last_name': address_data.get('lastName', ''),
                'company': address_data.get('company', ''),
                'address1': address_data.get('address1', ''),
                'address2': address_data.get('address2', ''),
                'city': address_data.get('city', ''),
                'province': address_data.get('province', ''),
                'country': address_data.get('country', ''),
                'zip_code': address_data.get('zip', ''),
                'phone': address_data.get('phone', ''),
                'province_code': address_data.get('provinceCode', ''),
                'country_code': address_data.get('countryCode', ''),
                'country_name': address_data.get('countryName', ''),
                'store_domain': self.store_domain,
            }
        )
        
        if not created:
            # Update existing address
            address.first_name = address_data.get('firstName', '')
            address.last_name = address_data.get('lastName', '')
            address.company = address_data.get('company', '')
            address.address1 = address_data.get('address1', '')
            address.address2 = address_data.get('address2', '')
            address.city = address_data.get('city', '')
            address.province = address_data.get('province', '')
            address.country = address_data.get('country', '')
            address.zip_code = address_data.get('zip', '')
            address.phone = address_data.get('phone', '')
            address.province_code = address_data.get('provinceCode', '')
            address.country_code = address_data.get('countryCode', '')
            address.country_name = address_data.get('countryName', '')
            address.save()
        
        return created
    
    def sync_customer_from_webhook(self, webhook_data):
        """Sync customer from webhook data"""
        try:
            created = self._sync_customer(webhook_data)
            logger.info(f"Customer {'created' if created else 'updated'} from webhook: {webhook_data.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error syncing customer from webhook: {e}")
            return False
