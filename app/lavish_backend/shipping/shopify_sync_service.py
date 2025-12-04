"""
Shopify Shipping Synchronization Service
Pulls carrier services, delivery profiles, zones, and shipping rates from Shopify
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from shopify_integration.client import ShopifyAPIClient
from .models import (
    ShopifyCarrierService,
    ShopifyDeliveryProfile,
    ShopifyDeliveryZone,
    ShopifyDeliveryMethod,
    ShippingRate,
    ShippingSyncLog,
    ShopifyFulfillmentOrder,
    FulfillmentTrackingInfo
)

logger = logging.getLogger(__name__)


class ShopifyShippingSyncService:
    """
    Service to sync shipping data from Shopify
    Pulls carrier services, delivery profiles, zones, methods, and rates
    """
    
    def __init__(self, shop_domain: Optional[str] = None, access_token: Optional[str] = None):
        self.shop_domain = shop_domain or getattr(settings, 'SHOPIFY_SHOP_DOMAIN', '7fa66c-ac.myshopify.com')
        self.access_token = access_token or getattr(settings, 'SHOPIFY_ACCESS_TOKEN', '')
        self.client = ShopifyAPIClient(self.shop_domain, self.access_token)
        self.sync_log = None
    
    def sync_all_shipping_data(self) -> Dict:
        """
        Sync all shipping-related data from Shopify
        
        Returns:
            Dict with sync results and statistics
        """
        logger.info(f"Starting full shipping data sync for {self.shop_domain}")
        
        # Create sync log
        self.sync_log = ShippingSyncLog.objects.create(
            operation_type='bulk_import',
            store_domain=self.shop_domain
        )
        
        results = {
            'carrier_services': 0,
            'delivery_profiles': 0,
            'delivery_zones': 0,
            'delivery_methods': 0,
            'shipping_rates': 0,
            'errors': []
        }
        
        try:
            # 1. Sync carrier services
            carrier_result = self.sync_carrier_services()
            results['carrier_services'] = carrier_result.get('synced', 0)
            if carrier_result.get('errors'):
                results['errors'].extend(carrier_result['errors'])
            
            # 2. Sync delivery profiles (includes zones and methods)
            profile_result = self.sync_delivery_profiles()
            results['delivery_profiles'] = profile_result.get('profiles', 0)
            results['delivery_zones'] = profile_result.get('zones', 0)
            results['delivery_methods'] = profile_result.get('methods', 0)
            if profile_result.get('errors'):
                results['errors'].extend(profile_result['errors'])
            
            # 3. Sync live shipping rates for each carrier
            rate_result = self.sync_shipping_rates()
            results['shipping_rates'] = rate_result.get('rates_synced', 0)
            if rate_result.get('errors'):
                results['errors'].extend(rate_result['errors'])
            
            # Update sync log
            self.sync_log.carriers_processed = results['carrier_services']
            self.sync_log.profiles_processed = results['delivery_profiles']
            self.sync_log.zones_processed = results['delivery_zones']
            self.sync_log.methods_processed = results['delivery_methods']
            self.sync_log.errors_count = len(results['errors'])
            self.sync_log.status = 'failed' if results['errors'] else 'completed'
            self.sync_log.completed_at = timezone.now()
            
            if results['errors']:
                self.sync_log.error_details = results['errors']
            
            self.sync_log.save()
            
            logger.info(f"Shipping sync complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Shipping sync failed: {str(e)}", exc_info=True)
            if self.sync_log:
                self.sync_log.status = 'failed'
                self.sync_log.error_details = {'error': str(e)}
                self.sync_log.completed_at = timezone.now()
                self.sync_log.save()
            
            results['errors'].append({'fatal_error': str(e)})
            return results
    
    def sync_carrier_services(self) -> Dict:
        """
        Sync carrier services from Shopify
        
        Returns:
            Dict with sync results
        """
        logger.info("Syncing carrier services from Shopify")
        
        results = {
            'synced': 0,
            'updated': 0,
            'created': 0,
            'errors': []
        }
        
        try:
            # REST API call to get carrier services
            response = self.client.rest_request('GET', '/carrier_services.json')
            
            if 'error' in response:
                logger.error(f"Failed to fetch carrier services: {response['error']}")
                results['errors'].append({'carrier_services': response['error']})
                return results
            
            carrier_services = response.get('carrier_services', [])
            logger.info(f"Found {len(carrier_services)} carrier services")
            
            for carrier_data in carrier_services:
                try:
                    shopify_id = str(carrier_data.get('id'))
                    
                    # Update or create carrier service
                    carrier, created = ShopifyCarrierService.objects.update_or_create(
                        shopify_id=shopify_id,
                        defaults={
                            'name': carrier_data.get('name'),
                            'active': carrier_data.get('active', True),
                            'service_discovery': carrier_data.get('service_discovery', False),
                            'carrier_service_type': carrier_data.get('carrier_service_type', 'api'),
                            'callback_url': carrier_data.get('callback_url', ''),
                            'format': carrier_data.get('format', 'json'),
                            'store_domain': self.shop_domain
                        }
                    )
                    
                    results['synced'] += 1
                    if created:
                        results['created'] += 1
                        logger.info(f"Created carrier service: {carrier.name}")
                    else:
                        results['updated'] += 1
                        logger.info(f"Updated carrier service: {carrier.name}")
                
                except Exception as e:
                    logger.error(f"Failed to sync carrier service {carrier_data.get('id')}: {str(e)}")
                    results['errors'].append({
                        'carrier_service': carrier_data.get('id'),
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Carrier services sync failed: {str(e)}", exc_info=True)
            results['errors'].append({'fatal_error': str(e)})
            return results
    
    def sync_delivery_profiles(self) -> Dict:
        """
        Sync delivery profiles (shipping zones and methods) from Shopify GraphQL
        
        Returns:
            Dict with sync results
        """
        logger.info("Syncing delivery profiles from Shopify")
        
        results = {
            'profiles': 0,
            'zones': 0,
            'methods': 0,
            'errors': []
        }
        
        try:
            # Simplified GraphQL query compatible with Shopify API 2024-10
            query = """
            query GetDeliveryProfiles {
              deliveryProfiles(first: 50) {
                nodes {
                  id
                  name
                  default
                  profileLocationGroups {
                    locationGroupZones(first: 50) {
                      nodes {
                        zone {
                          id
                          name
                          countries {
                            code {
                              countryCode
                            }
                            name
                          }
                        }
                        methodDefinitions(first: 50) {
                          nodes {
                            id
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            response = self.client.execute_graphql_query(query)
            
            if 'error' in response:
                logger.error(f"GraphQL query failed: {response['error']}")
                results['errors'].append({'delivery_profiles': response['error']})
                return results
            
            if 'errors' in response:
                logger.error(f"GraphQL errors: {response['errors']}")
                results['errors'].append({'graphql_errors': response['errors']})
                return results
            
            profiles = response.get('data', {}).get('deliveryProfiles', {}).get('nodes', [])
            logger.info(f"Found {len(profiles)} delivery profiles")
            
            for profile_data in profiles:
                try:
                    # Create/update delivery profile
                    profile_result = self._sync_delivery_profile(profile_data)
                    
                    results['profiles'] += 1
                    results['zones'] += profile_result['zones']
                    results['methods'] += profile_result['methods']
                    
                except Exception as e:
                    logger.error(f"Failed to sync delivery profile: {str(e)}")
                    results['errors'].append({
                        'profile': profile_data.get('id'),
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Delivery profiles sync failed: {str(e)}", exc_info=True)
            results['errors'].append({'fatal_error': str(e)})
            return results
    
    def _sync_delivery_profile(self, profile_data: Dict) -> Dict:
        """
        Sync a single delivery profile with its zones and methods
        
        Returns:
            Dict with counts of synced zones and methods
        """
        shopify_id = profile_data['id'].split('/')[-1]
        
        # Create/update profile
        profile, created = ShopifyDeliveryProfile.objects.update_or_create(
            shopify_id=shopify_id,
            defaults={
                'name': profile_data.get('name'),
                'active': True,
                'default': profile_data.get('default', False),
                'locations_without_rates_to_ship': [],
                'store_domain': self.shop_domain
            }
        )
        
        logger.info(f"{'Created' if created else 'Updated'} delivery profile: {profile.name}")
        
        result = {'zones': 0, 'methods': 0}
        
        # Sync zones and methods
        location_groups = profile_data.get('profileLocationGroups', [])
        
        for group in location_groups:
            zones = group.get('locationGroupZones', {}).get('nodes', [])
            
            for zone_data in zones:
                zone_info = zone_data.get('zone', {})
                zone_shopify_id = zone_info['id'].split('/')[-1]
                
                # Get countries list
                countries = []
                for country in zone_info.get('countries', []):
                    code = country.get('code', {})
                    countries.append({
                        'country_code': code.get('countryCode'),
                        'name': country.get('name')
                    })
                
                # Create/update zone
                zone, zone_created = ShopifyDeliveryZone.objects.update_or_create(
                    shopify_id=zone_shopify_id,
                    defaults={
                        'profile': profile,
                        'name': zone_info.get('name'),
                        'countries': countries,
                        'store_domain': self.shop_domain
                    }
                )
                
                result['zones'] += 1
                logger.debug(f"{'Created' if zone_created else 'Updated'} zone: {zone.name}")
                
                # Sync methods for this zone
                methods = zone_data.get('methodDefinitions', {}).get('nodes', [])
                
                for method_data in methods:
                    method_shopify_id = method_data['id'].split('/')[-1]
                    
                    # Create/update method
                    method, method_created = ShopifyDeliveryMethod.objects.update_or_create(
                        shopify_id=method_shopify_id,
                        defaults={
                            'zone': zone,
                            'name': method_data.get('name'),
                            'method_type': 'shipping',  # Default to shipping
                            'store_domain': self.shop_domain
                        }
                    )
                    
                    result['methods'] += 1
                    logger.debug(f"{'Created' if method_created else 'Updated'} method: {method.name}")
        
        return result
    
    def get_shipping_rates_for_address(self, origin: Dict, destination: Dict, items: List[Dict]) -> Dict:
        """
        Get shipping rates from Shopify for specific addresses and items
        This queries Shopify's configured shipping rates
        
        Args:
            origin: Origin address dict (country, postal_code, province, city)
            destination: Destination address dict
            items: List of items with grams, price, quantity
            
        Returns:
            Dict with available shipping rates
        """
        logger.info(f"Fetching Shopify shipping rates for {destination.get('country')}")
        
        try:
            # Use REST API to get shipping rates
            # Note: This endpoint requires the order to exist or use draft orders
            # For real-time rates during checkout, use carrier service callback instead
            
            # Alternative: Query delivery profiles to find applicable rates
            destination_country = destination.get('country')
            
            # Find applicable delivery zones
            zones = ShopifyDeliveryZone.objects.filter(
                countries__icontains=destination_country,
                store_domain=self.shop_domain
            )
            
            rates = []
            
            for zone in zones:
                methods = zone.methods.all()
                
                for method in methods:
                    rates.append({
                        'service_name': method.name,
                        'service_code': method.shopify_id,
                        'zone': zone.name,
                        'profile': zone.profile.name
                    })
            
            return {
                'success': True,
                'rates': rates,
                'destination': destination_country
            }
            
        except Exception as e:
            logger.error(f"Failed to get shipping rates: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_carrier_service_details(self, carrier_service_id: str) -> Dict:
        """
        Get detailed information about a specific carrier service
        
        Args:
            carrier_service_id: Shopify carrier service ID
            
        Returns:
            Dict with carrier service details
        """
        try:
            response = self.client.rest_request('GET', f'/carrier_services/{carrier_service_id}.json')
            
            if 'error' in response:
                logger.error(f"Failed to fetch carrier service: {response['error']}")
                return {'error': response['error']}
            
            carrier_service = response.get('carrier_service', {})
            
            return {
                'success': True,
                'carrier_service': {
                    'id': carrier_service.get('id'),
                    'name': carrier_service.get('name'),
                    'active': carrier_service.get('active'),
                    'service_discovery': carrier_service.get('service_discovery'),
                    'carrier_service_type': carrier_service.get('carrier_service_type'),
                    'callback_url': carrier_service.get('callback_url'),
                    'format': carrier_service.get('format'),
                    'admin_graphql_api_id': carrier_service.get('admin_graphql_api_id')
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get carrier service details: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def sync_shipping_rates(self, sample_destinations: Optional[List[str]] = None) -> Dict:
        """
        Sync shipping rates from Shopify delivery methods.
        
        Extracts rate information from configured delivery methods and stores them
        in a normalized format for easy querying and display in Django admin.
        For Shopify stores, the "rates" come from delivery methods which include:
        - Fixed price rates (flat rate shipping)
        - Carrier-calculated rates (referenced but calculated at checkout)
        - Free shipping rules
        
        Args:
            sample_destinations: Not used (kept for API compatibility)
            
        Returns:
            Dict with sync statistics
        """
        from decimal import Decimal
        from shipping.models import ShippingRate, ShopifyDeliveryMethod
        
        logger.info("Starting shipping rates sync from delivery methods")
        
        results = {
            'rates_synced': 0,
            'rates_created': 0,
            'rates_updated': 0,
            'methods_processed': 0,
            'errors': []
        }
        
        try:
            # Get all delivery methods
            methods = ShopifyDeliveryMethod.objects.all()
            
            for method in methods:
                try:
                    results['methods_processed'] += 1
                    
                    # Extract zone and profile info
                    zone = method.zone
                    profile = zone.profile
                    
                    # Get countries from zone
                    countries = []
                    if zone.countries:
                        for country in zone.countries:
                            if isinstance(country, dict):
                                if 'code' in country and 'countryCode' in country['code']:
                                    countries.append(country['code']['countryCode'])
                                elif 'countryCode' in country:
                                    countries.append(country['countryCode'])
                            elif isinstance(country, str):
                                countries.append(country)
                    
                    # If no specific countries, mark as "WORLDWIDE"
                    if not countries:
                        countries = ['WORLDWIDE']
                    
                    # Create a rate entry for each country in the zone
                    for country_code in countries:
                        # Try to match a carrier service based on method name
                        carrier = None
                        method_name_lower = method.name.lower()
                        
                        # Try to find a matching carrier
                        carriers = ShopifyCarrierService.objects.filter(active=True)
                        for c in carriers:
                            carrier_name_lower = c.name.lower()
                            # Check if carrier name is in method name
                            if carrier_name_lower in method_name_lower:
                                carrier = c
                                break
                        
                        # If no match, try to infer from common shipping terms
                        if not carrier:
                            if 'usps' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='usps', active=True).first()
                            elif 'ups' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='ups', active=True).first()
                            elif 'dhl' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='dhl', active=True).first()
                            elif 'fedex' in method_name_lower or 'fed ex' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='fedex', active=True).first()
                            elif 'australia post' in method_name_lower or 'auspost' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='australia_post', active=True).first()
                            elif 'canada post' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='canada', active=True).first()
                            elif 'royal mail' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='royal', active=True).first()
                            elif 'sendle' in method_name_lower:
                                carrier = ShopifyCarrierService.objects.filter(name__icontains='sendle', active=True).first()
                        
                        # Determine pricing based on method name (many merchants include price in name)
                        price_amount = Decimal('0.00')
                        title = method.name
                        description = f"{profile.name} - {zone.name}"
                        handle = f"{method.shopify_id}".replace('gid://shopify/DeliveryMethodDefinition/', '').replace('gid://shopify/DeliveryMethod/', '').strip('/')
                        
                        # Try to extract price from method name (common patterns: $10, $10.99, €5, £8)
                        import re
                        price_match = re.search(r'[$€£¥]\s*(\d+\.?\d*)', method.name)
                        if price_match and price_match.group(1):
                            try:
                                price_amount = Decimal(price_match.group(1))
                            except (ValueError, Exception):
                                pass
                        
                        # Determine currency from country
                        currency_map = {
                            'US': 'USD', 'CA': 'CAD', 'GB': 'GBP', 'AU': 'AUD',
                            'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR',
                            'JP': 'JPY', 'CN': 'CNY', 'IN': 'INR', 'MX': 'MXN', 'BR': 'BRL',
                            'WORLDWIDE': 'USD'
                        }
                        currency = currency_map.get(country_code, 'USD')
                        
                        # Estimate delivery times from method timing data
                        min_days = None
                        max_days = None
                        if method.min_delivery_date_time and method.max_delivery_date_time:
                            from datetime import datetime, timezone as tz
                            now = datetime.now(tz.utc)
                            try:
                                min_days = max(0, (method.min_delivery_date_time - now).days)
                                max_days = max(0, (method.max_delivery_date_time - now).days)
                            except:
                                pass
                        
                        # Create or update shipping rate
                        shipping_rate, created = ShippingRate.objects.update_or_create(
                            delivery_method=method,
                            destination_country=country_code,
                            defaults={
                                'carrier': carrier,  # Now linked to matched carrier
                                'handle': handle,
                                'title': title,
                                'price_amount': price_amount,
                                'price_currency': currency,
                                'description': description,
                                'service_code': method.method_type.upper(),
                                'origin_country': 'US',  # Default - update based on your store location
                                'destination_zone': zone.name,
                                'phone_required': False,
                                'active': True,
                                'store_domain': self.shop_domain,
                                'min_delivery_days': min_days,
                                'max_delivery_days': max_days,
                            }
                        )
                        
                        results['rates_synced'] += 1
                        if created:
                            results['rates_created'] += 1
                            logger.debug(f"Created rate: {title} for {country_code}")
                        else:
                            results['rates_updated'] += 1
                            logger.debug(f"Updated rate: {title} for {country_code}")
                
                except Exception as e:
                    error_msg = f"Failed to process method {method.name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Synced {results['rates_synced']} rates from {results['methods_processed']} delivery methods ({results['rates_created']} created, {results['rates_updated']} updated)")
            return results
            
        except Exception as e:
            error_msg = f"Rate sync failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            return results
    
    def _get_sample_postal_code(self, country_code: str) -> str:
        """Get a sample postal code for a country"""
        postal_codes = {
            'US': '10001',
            'CA': 'M5H2N2',
            'GB': 'SW1A1AA',
            'AU': '2000',
            'DE': '10115',
            'FR': '75001',
            'JP': '100-0001',
        }
        return postal_codes.get(country_code, '00000')
    
    def _get_currency_for_country(self, country_code: str) -> str:
        """Get currency code for a country"""
        currencies = {
            'US': 'USD',
            'CA': 'CAD',
            'GB': 'GBP',
            'AU': 'AUD',
            'DE': 'EUR',
            'FR': 'EUR',
            'JP': 'JPY',
        }
        return currencies.get(country_code, 'USD')
    
    def sync_fulfillment_orders(self, order_ids: Optional[List[str]] = None) -> Dict:
        """
        Sync fulfillment orders from Shopify orders.
        
        Fulfillment orders represent the actual shipment logistics for orders.
        Each order can have multiple fulfillment orders (split shipments).
        This method pulls fulfillment order data including tracking info.
        
        Args:
            order_ids: Optional list of specific Shopify order IDs to sync.
                      If None, syncs fulfillment orders for all orders in database.
        
        Returns:
            Dict with sync statistics
        """
        from orders.models import ShopifyOrder
        from django.utils.dateparse import parse_datetime
        
        logger.info("Starting fulfillment orders sync from Shopify")
        
        results = {
            'fulfillment_orders_synced': 0,
            'fulfillment_orders_created': 0,
            'fulfillment_orders_updated': 0,
            'tracking_info_synced': 0,
            'tracking_info_created': 0,
            'tracking_info_updated': 0,
            'orders_processed': 0,
            'errors': []
        }
        
        try:
            # Get orders to process
            if order_ids:
                orders = ShopifyOrder.objects.filter(shopify_id__in=order_ids)
            else:
                # Sync for all orders that have fulfillment status (likely to have fulfillment orders)
                # Limit to 20 to avoid API timeouts
                orders = ShopifyOrder.objects.exclude(fulfillment_status='null')[:20]
            
            logger.info(f"Processing fulfillment orders for {orders.count()} orders")
            
            import time  # For rate limiting
            
            for order in orders:
                try:
                    results['orders_processed'] += 1
                    
                    # Add small delay to avoid overwhelming API
                    time.sleep(0.5)  # 500ms between requests
                    
                    # Extract numeric ID from Shopify GID
                    numeric_id = order.shopify_id.split('/')[-1]
                    
                    # Query Shopify for fulfillment orders
                    query = """
                    query getFulfillmentOrders($orderId: ID!) {
                        order(id: $orderId) {
                            id
                            fulfillmentOrders(first: 10) {
                                edges {
                                    node {
                                        id
                                        status
                                        requestStatus
                                        fulfillAt
                                        fulfillBy
                                        deliveryMethod {
                                            methodType
                                            minDeliveryDateTime
                                            maxDeliveryDateTime
                                        }
                                        internationalDuties {
                                            incoterm
                                        }
                                        assignedLocation {
                                            location {
                                                id
                                                name
                                            }
                                        }
                                        createdAt
                                        updatedAt
                                    }
                                }
                            }
                            fulfillments {
                                trackingInfo {
                                    company
                                    number
                                    url
                                }
                            }
                        }
                    }
                    """
                    
                    variables = {
                        'orderId': order.shopify_id
                    }
                    
                    response = self.client.execute_graphql_query(query, variables)
                    
                    if not response or 'data' not in response or not response['data'].get('order'):
                        logger.debug(f"No fulfillment data for order {order.order_number}")
                        continue
                    
                    fulfillment_orders_data = response['data']['order'].get('fulfillmentOrders', {}).get('edges', [])
                    fulfillments_data = response['data']['order'].get('fulfillments', [])
                    
                    if not fulfillment_orders_data:
                        logger.debug(f"No fulfillment orders for order {order.order_number}")
                        continue
                    
                    # Process each fulfillment order
                    for edge in fulfillment_orders_data:
                        node = edge.get('node', {})
                        
                        # Parse timestamps
                        created_at = parse_datetime(node.get('createdAt'))
                        updated_at = parse_datetime(node.get('updatedAt'))
                        fulfill_at = parse_datetime(node.get('fulfillAt')) if node.get('fulfillAt') else None
                        fulfill_by = parse_datetime(node.get('fulfillBy')) if node.get('fulfillBy') else None
                        
                        # Get location
                        location = None
                        assigned_location = node.get('assignedLocation', {})
                        if assigned_location and assigned_location.get('location'):
                            location_id = assigned_location['location'].get('id')
                            if location_id:
                                from inventory.models import ShopifyLocation
                                location = ShopifyLocation.objects.filter(shopify_id=location_id).first()
                        
                        # Create or update fulfillment order
                        fulfillment_order, created = ShopifyFulfillmentOrder.objects.update_or_create(
                            shopify_id=node['id'],
                            defaults={
                                'order': order,
                                'location': location,
                                'status': node.get('status', 'open').lower(),
                                'request_status': node.get('requestStatus', 'unsubmitted').lower(),
                                'fulfill_at': fulfill_at,
                                'fulfill_by': fulfill_by,
                                'international_duties': node.get('internationalDuties'),
                                'delivery_method': node.get('deliveryMethod'),
                                'created_at': created_at,
                                'updated_at': updated_at,
                                'store_domain': self.shop_domain,
                            }
                        )
                        
                        results['fulfillment_orders_synced'] += 1
                        if created:
                            results['fulfillment_orders_created'] += 1
                            logger.debug(f"Created fulfillment order {node['id']}")
                        else:
                            results['fulfillment_orders_updated'] += 1
                            logger.debug(f"Updated fulfillment order {node['id']}")
                    
                    # Process tracking info from order's fulfillments (not from fulfillment_orders)
                    for fulfillment in fulfillments_data:
                        tracking_info_list = fulfillment.get('trackingInfo', [])
                        
                        for tracking_info in tracking_info_list:
                            company = tracking_info.get('company', '')
                            number = tracking_info.get('number', '')
                            url = tracking_info.get('url', '')
                            
                            if not number:
                                continue  # Skip if no tracking number
                            
                            # Link tracking to the first fulfillment order (most common case)
                            # In reality, we'd need to match fulfillment to fulfillment_order via line items
                            if fulfillment_orders_data:
                                first_fo_node = fulfillment_orders_data[0]['node']
                                fulfillment_order = ShopifyFulfillmentOrder.objects.filter(
                                    shopify_id=first_fo_node['id']
                                ).first()
                                
                                if fulfillment_order:
                                    # Create or update tracking info
                                    tracking, tracking_created = FulfillmentTrackingInfo.objects.update_or_create(
                                        fulfillment_order=fulfillment_order,
                                        number=number,
                                        defaults={
                                            'company': company,
                                            'url': url,
                                            'is_active': True,
                                        }
                                    )
                                    
                                    results['tracking_info_synced'] += 1
                                    if tracking_created:
                                        results['tracking_info_created'] += 1
                                        logger.debug(f"Created tracking info: {company} - {number}")
                                    else:
                                        results['tracking_info_updated'] += 1
                                        logger.debug(f"Updated tracking info: {company} - {number}")
                
                except Exception as e:
                    error_msg = f"Failed to process order {order.order_number}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
            
            logger.info(f"Fulfillment sync complete: {results['fulfillment_orders_synced']} fulfillment orders, {results['tracking_info_synced']} tracking records")
            return results
            
        except Exception as e:
            error_msg = f"Fulfillment sync failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            return results
