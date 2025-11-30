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
        
        # If nothing specified, sync everything
        if not sync_carriers and not sync_profiles:
            sync_carriers = True
            sync_profiles = True
        
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
