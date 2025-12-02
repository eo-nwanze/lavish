"""
Django management command to sync shipping data from Shopify
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from shipping.shopify_sync_service import ShopifyShippingSyncService
from shipping.models import ShopifyCarrierService, ShopifyDeliveryProfile, ShopifyDeliveryZone
import json


class Command(BaseCommand):
    help = 'Sync shipping data from Shopify (carrier services, delivery profiles, zones, methods)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--carrier-services',
            action='store_true',
            help='Sync only carrier services',
        )
        parser.add_argument(
            '--delivery-profiles',
            action='store_true',
            help='Sync only delivery profiles (includes zones and methods)',
        )
        parser.add_argument(
            '--rates',
            action='store_true',
            help='Sync only shipping rates from delivery methods',
        )
        parser.add_argument(
            '--fulfillment-orders',
            action='store_true',
            help='Sync fulfillment orders and tracking info from Shopify orders',
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Show detailed information after sync',
        )
        parser.add_argument(
            '--carrier-id',
            type=str,
            help='Get details for a specific carrier service ID',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('SHOPIFY SHIPPING DATA SYNC'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        service = ShopifyShippingSyncService()
        
        # Check if we're getting details for a specific carrier
        if options['carrier_id']:
            self.get_carrier_details(service, options['carrier_id'])
            return
        
        # Determine what to sync
        sync_carriers = options['carrier_services']
        sync_profiles = options['delivery_profiles']
        sync_rates = options['rates']
        sync_fulfillment = options['fulfillment_orders']
        
        # If nothing specified, sync everything
        if not sync_carriers and not sync_profiles and not sync_rates and not sync_fulfillment:
            sync_carriers = True
            sync_profiles = True
            sync_rates = True
            # Don't auto-sync fulfillment orders (can be slow with many orders)
            sync_fulfillment = False
        
        results = {}
        
        try:
            if sync_carriers:
                self.stdout.write(self.style.WARNING('Syncing carrier services...'))
                carrier_results = service.sync_carrier_services()
                results['carrier_services'] = carrier_results
                self.print_carrier_results(carrier_results)
            
            if sync_profiles:
                self.stdout.write(self.style.WARNING('Syncing delivery profiles...'))
                profile_results = service.sync_delivery_profiles()
                results['delivery_profiles'] = profile_results
                self.print_profile_results(profile_results)
            
            if sync_rates:
                self.stdout.write(self.style.WARNING('Syncing shipping rates...'))
                rate_results = service.sync_shipping_rates()
                results['shipping_rates'] = rate_results
                self.print_rate_results(rate_results)
            
            if sync_fulfillment:
                self.stdout.write(self.style.WARNING('Syncing fulfillment orders and tracking info...'))
                fulfillment_results = service.sync_fulfillment_orders()
                results['fulfillment_orders'] = fulfillment_results
                self.print_fulfillment_results(fulfillment_results)
            
            # Show summary
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(self.style.SUCCESS('SYNC SUMMARY'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
            total_errors = 0
            
            if 'carrier_services' in results:
                cs = results['carrier_services']
                self.stdout.write(f"Carrier Services: {cs['synced']} synced ({cs['created']} created, {cs['updated']} updated)")
                total_errors += len(cs.get('errors', []))
            
            if 'delivery_profiles' in results:
                dp = results['delivery_profiles']
                self.stdout.write(f"Delivery Profiles: {dp['profiles']} profiles, {dp['zones']} zones, {dp['methods']} methods")
                total_errors += len(dp.get('errors', []))
            
            if 'shipping_rates' in results:
                sr = results['shipping_rates']
                self.stdout.write(f"Shipping Rates: {sr['rates_synced']} rates synced ({sr['rates_created']} created, {sr['rates_updated']} updated) from {sr['methods_processed']} methods")
                total_errors += len(sr.get('errors', []))
            
            if 'fulfillment_orders' in results:
                fo = results['fulfillment_orders']
                self.stdout.write(f"Fulfillment Orders: {fo['fulfillment_orders_synced']} orders ({fo['fulfillment_orders_created']} created, {fo['fulfillment_orders_updated']} updated)")
                self.stdout.write(f"Tracking Info: {fo['tracking_info_synced']} records ({fo['tracking_info_created']} created, {fo['tracking_info_updated']} updated)")
                total_errors += len(fo.get('errors', []))
            
            if total_errors > 0:
                self.stdout.write(self.style.ERROR(f"Total Errors: {total_errors}"))
                self.stdout.write(self.style.ERROR("Check logs for details"))
            else:
                self.stdout.write(self.style.SUCCESS("✓ Sync completed successfully with no errors"))
            
            # Show detailed information if requested
            if options['show_details']:
                self.show_synced_data()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sync failed: {str(e)}"))
            raise
    
    def print_carrier_results(self, results):
        """Print carrier service sync results"""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Carrier Services:'))
        self.stdout.write(f"  - Synced: {results['synced']}")
        self.stdout.write(f"  - Created: {results['created']}")
        self.stdout.write(f"  - Updated: {results['updated']}")
        
        if results.get('errors'):
            self.stdout.write(self.style.ERROR(f"  - Errors: {len(results['errors'])}"))
            for error in results['errors'][:5]:  # Show first 5 errors
                self.stdout.write(self.style.ERROR(f"    • {error}"))
        else:
            self.stdout.write(self.style.SUCCESS("  - No errors"))
        
        self.stdout.write('')
    
    def print_profile_results(self, results):
        """Print delivery profile sync results"""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Delivery Profiles:'))
        self.stdout.write(f"  - Profiles: {results['profiles']}")
        self.stdout.write(f"  - Zones: {results['zones']}")
        self.stdout.write(f"  - Methods: {results['methods']}")
        
        if results.get('errors'):
            self.stdout.write(self.style.ERROR(f"  - Errors: {len(results['errors'])}"))
            for error in results['errors'][:5]:  # Show first 5 errors
                self.stdout.write(self.style.ERROR(f"    • {error}"))
        else:
            self.stdout.write(self.style.SUCCESS("  - No errors"))
        
        self.stdout.write('')
    
    def print_rate_results(self, results):
        """Print shipping rate sync results"""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Shipping Rates:'))
        self.stdout.write(f"  - Methods Processed: {results['methods_processed']}")
        self.stdout.write(f"  - Rates Synced: {results['rates_synced']}")
        self.stdout.write(f"  - Created: {results['rates_created']}")
        self.stdout.write(f"  - Updated: {results['rates_updated']}")
        
        if results.get('errors'):
            self.stdout.write(self.style.ERROR(f"  - Errors: {len(results['errors'])}"))
            for error in results['errors'][:5]:  # Show first 5 errors
                self.stdout.write(self.style.ERROR(f"    • {error}"))
        else:
            self.stdout.write(self.style.SUCCESS("  - No errors"))
        
        self.stdout.write('')
    
    def print_fulfillment_results(self, results):
        """Print fulfillment order sync results"""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Fulfillment Orders & Tracking:'))
        self.stdout.write(f"  - Orders Processed: {results['orders_processed']}")
        self.stdout.write(f"  - Fulfillment Orders Synced: {results['fulfillment_orders_synced']}")
        self.stdout.write(f"    • Created: {results['fulfillment_orders_created']}")
        self.stdout.write(f"    • Updated: {results['fulfillment_orders_updated']}")
        self.stdout.write(f"  - Tracking Info Synced: {results['tracking_info_synced']}")
        self.stdout.write(f"    • Created: {results['tracking_info_created']}")
        self.stdout.write(f"    • Updated: {results['tracking_info_updated']}")
        
        if results.get('errors'):
            self.stdout.write(self.style.ERROR(f"  - Errors: {len(results['errors'])}"))
            for error in results['errors'][:5]:  # Show first 5 errors
                self.stdout.write(self.style.ERROR(f"    • {error}"))
        else:
            self.stdout.write(self.style.SUCCESS("  - No errors"))
        
        self.stdout.write('')
    
    def show_synced_data(self):
        """Show detailed information about synced data"""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('SYNCED DATA DETAILS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # Show carrier services
        carriers = ShopifyCarrierService.objects.all()
        if carriers.exists():
            self.stdout.write(self.style.WARNING('Carrier Services:'))
            for carrier in carriers:
                status = '✓ Active' if carrier.active else '✗ Inactive'
                self.stdout.write(f"  • {carrier.name} [{status}]")
                self.stdout.write(f"    ID: {carrier.shopify_id}")
                self.stdout.write(f"    Type: {carrier.carrier_service_type}")
                self.stdout.write(f"    Callback: {carrier.callback_url or 'N/A'}")
                self.stdout.write(f"    Service Discovery: {carrier.service_discovery}")
                self.stdout.write('')
        
        # Show delivery profiles
        profiles = ShopifyDeliveryProfile.objects.all()
        if profiles.exists():
            self.stdout.write(self.style.WARNING('Delivery Profiles:'))
            for profile in profiles:
                default_marker = ' [DEFAULT]' if profile.default else ''
                self.stdout.write(f"  • {profile.name}{default_marker}")
                self.stdout.write(f"    ID: {profile.shopify_id}")
                
                # Show zones
                zones = profile.zones.all()
                if zones.exists():
                    self.stdout.write(f"    Zones: {zones.count()}")
                    for zone in zones:
                        countries = ', '.join([c.get('country_code', 'N/A') for c in zone.countries[:5]])
                        if len(zone.countries) > 5:
                            countries += f" +{len(zone.countries) - 5} more"
                        
                        self.stdout.write(f"      - {zone.name}: {countries}")
                        
                        # Show methods
                        methods = zone.methods.all()
                        if methods.exists():
                            self.stdout.write(f"        Methods: {methods.count()}")
                            for method in methods[:3]:  # Show first 3 methods
                                self.stdout.write(f"          • {method.name} ({method.method_type})")
                            
                            if methods.count() > 3:
                                self.stdout.write(f"          ... and {methods.count() - 3} more")
                
                self.stdout.write('')
    
    def get_carrier_details(self, service, carrier_id):
        """Get and display details for a specific carrier service"""
        self.stdout.write(self.style.WARNING(f'Fetching details for carrier service: {carrier_id}'))
        self.stdout.write('')
        
        result = service.get_carrier_service_details(carrier_id)
        
        if 'error' in result:
            self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))
            return
        
        carrier = result['carrier_service']
        
        self.stdout.write(self.style.SUCCESS('Carrier Service Details:'))
        self.stdout.write('')
        self.stdout.write(f"ID: {carrier['id']}")
        self.stdout.write(f"Name: {carrier['name']}")
        self.stdout.write(f"Active: {carrier['active']}")
        self.stdout.write(f"Service Discovery: {carrier['service_discovery']}")
        self.stdout.write(f"Type: {carrier['carrier_service_type']}")
        self.stdout.write(f"Callback URL: {carrier['callback_url']}")
        self.stdout.write(f"Format: {carrier['format']}")
        self.stdout.write(f"GraphQL API ID: {carrier['admin_graphql_api_id']}")
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('✓ Details retrieved successfully'))
