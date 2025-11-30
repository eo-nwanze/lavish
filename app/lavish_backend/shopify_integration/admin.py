from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.html import format_html
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db import models
from django.template.response import TemplateResponse
import threading
import time
from datetime import datetime

# Import sync functions
from .enhanced_client import EnhancedShopifyAPIClient


class ShopifyIntegrationAdminView(admin.ModelAdmin):
    """Shopify Integration Control Panel"""
    
    change_list_template = 'admin/shopify_sync_dashboard.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sync-all/', self.admin_site.admin_view(self.sync_all_data), name='shopify_sync_all'),
            path('sync-customers/', self.admin_site.admin_view(self.sync_customers), name='shopify_sync_customers'),
            path('sync-products/', self.admin_site.admin_view(self.sync_products), name='shopify_sync_products'),
            path('sync-orders/', self.admin_site.admin_view(self.sync_orders), name='shopify_sync_orders'),
            path('sync-inventory/', self.admin_site.admin_view(self.sync_inventory), name='shopify_sync_inventory'),
            path('sync-shipping/', self.admin_site.admin_view(self.sync_shipping), name='shopify_sync_shipping'),
            path('sync-payments/', self.admin_site.admin_view(self.sync_payments), name='shopify_sync_payments'),
            path('sync-webhooks/', self.admin_site.admin_view(self.sync_webhooks), name='shopify_sync_webhooks'),
            path('sync-status/', self.admin_site.admin_view(self.sync_status), name='shopify_sync_status'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist to show sync dashboard"""
        # Get current data counts
        from customers.models import ShopifyCustomer, ShopifyCustomerAddress
        from products.models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage
        from orders.models import ShopifyOrder, ShopifyOrderLineItem
        from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel
        from shipping.models import ShopifyCarrierService, ShopifyDeliveryProfile
        from payments.models import ShopifyPaymentsAccount, ShopifyBalanceTransaction, ShopifyPayout, ShopifyDispute, ShopifyFinanceKYC
        from subscriptions.models import ShopifyWebhookSubscription, ShopifyWebhookDelivery
        
        # Get recent product images for gallery
        product_images = ShopifyProductImage.objects.select_related('product').order_by('-created_at')[:12]
        
        context = {
            'title': 'Shopify Integration Dashboard',
            'has_permission': True,
            'app_label': 'shopify_integration',
            'data_counts': {
                'customers': ShopifyCustomer.objects.count(),
                'customer_addresses': ShopifyCustomerAddress.objects.count(),
                'products': ShopifyProduct.objects.count(),
                'product_variants': ShopifyProductVariant.objects.count(),
                'product_images': ShopifyProductImage.objects.count(),
                'orders': ShopifyOrder.objects.count(),
                'order_line_items': ShopifyOrderLineItem.objects.count(),
                'inventory_items': ShopifyInventoryItem.objects.count(),
                'inventory_levels': ShopifyInventoryLevel.objects.count(),
                'carrier_services': ShopifyCarrierService.objects.count(),
                'delivery_profiles': ShopifyDeliveryProfile.objects.count(),
                'payments_accounts': ShopifyPaymentsAccount.objects.count(),
                'balance_transactions': ShopifyBalanceTransaction.objects.count(),
                'payouts': ShopifyPayout.objects.count(),
                'disputes': ShopifyDispute.objects.count(),
                'kyc_info': ShopifyFinanceKYC.objects.count(),
                'webhook_subscriptions': ShopifyWebhookSubscription.objects.count(),
                'webhook_deliveries': ShopifyWebhookDelivery.objects.count(),
            },
            'product_images': product_images,
        }
        
        if extra_context:
            context.update(extra_context)
            
        return TemplateResponse(request, self.change_list_template, context)
    
    def sync_all_data(self, request):
        """Sync all data from Shopify"""
        if request.method == 'POST':
            try:
                # Start background sync
                thread = threading.Thread(target=self._background_sync_all)
                thread.daemon = True
                thread.start()
                
                messages.success(request, 'Full sync started in background!')
                return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
            except Exception as e:
                messages.error(request, f'Failed to start sync: {str(e)}')
                return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
        
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_customers(self, request):
        """Sync customers only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_customers)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Customer sync started!')
            except Exception as e:
                messages.error(request, f'Customer sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_products(self, request):
        """Sync products only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_products)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Product sync started!')
            except Exception as e:
                messages.error(request, f'Product sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_orders(self, request):
        """Sync orders only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_orders)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Order sync started!')
            except Exception as e:
                messages.error(request, f'Order sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_inventory(self, request):
        """Sync inventory only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_inventory)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Inventory sync started!')
            except Exception as e:
                messages.error(request, f'Inventory sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_shipping(self, request):
        """Sync shipping only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_shipping)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Shipping sync started!')
            except Exception as e:
                messages.error(request, f'Shipping sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_payments(self, request):
        """Sync payments only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_payments)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Payments sync started!')
            except Exception as e:
                messages.error(request, f'Payments sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_webhooks(self, request):
        """Sync webhook subscriptions only"""
        if request.method == 'POST':
            try:
                thread = threading.Thread(target=self._background_sync_webhooks)
                thread.daemon = True
                thread.start()
                messages.success(request, 'Webhook subscriptions sync started!')
            except Exception as e:
                messages.error(request, f'Webhook sync failed: {str(e)}')
        return redirect('admin:shopify_integration_shopifyintegrationdashboard_changelist')
    
    def sync_status(self, request):
        """Get sync status"""
        return JsonResponse({
            'status': 'idle',
            'last_sync': datetime.now().isoformat(),
            'message': 'No active sync operations'
        })
    
    # Background sync methods
    def _background_sync_all(self):
        """Background sync all data with progress tracking"""
        try:
            print("\n" + "="*80)
            print("INITIATING FULL SHOPIFY SYNC SEQUENCE")
            print("="*80)
            
            client = EnhancedShopifyAPIClient()
            
            # Progress tracking
            total_steps = 6
            current_step = 0
            
            # Step 1: Customers
            current_step += 1
            self._show_progress("CUSTOMERS", current_step, total_steps)
            self._sync_customers_data(client)
            
            # Step 2: Products
            current_step += 1
            self._show_progress("PRODUCTS", current_step, total_steps)
            self._sync_products_data(client)
            
            # Step 3: Orders
            current_step += 1
            self._show_progress("ORDERS", current_step, total_steps)
            self._sync_orders_data(client)
            
            # Step 4: Inventory
            current_step += 1
            self._show_progress("INVENTORY", current_step, total_steps)
            self._sync_inventory_data(client)
            
            # Step 5: Shipping
            current_step += 1
            self._show_progress("SHIPPING", current_step, total_steps)
            self._sync_shipping_data(client)
            
            # Step 6: Payments
            current_step += 1
            self._show_progress("PAYMENTS", current_step, total_steps)
            self._sync_payments_data(client)
            
            print("\n" + "="*80)
            print("FULL SYNC SEQUENCE COMPLETED SUCCESSFULLY")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ SYNC ERROR: {e}")
            print("="*80)
    
    def _show_progress(self, operation, current, total):
        """Show Hollywood-style progress bar"""
        percentage = (current / total) * 100
        filled = int(percentage // 2)
        bar = "█" * filled + "░" * (50 - filled)
        
        print(f"\nSYNCING {operation}")
        print(f"[{bar}] {percentage:.1f}% ({current}/{total})")
        print(f"Processing {operation.lower()} data from Shopify...")
        
        # Simulate some processing time for visual effect
        time.sleep(0.5)
    
    def _background_sync_customers(self):
        """Background sync customers with progress"""
        try:
            print("\n" + "="*60)
            print("CUSTOMER SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("CUSTOMERS", 1, 1)
            self._sync_customers_data(client)
            
            print("CUSTOMER SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Customer sync error: {e}")
    
    def _background_sync_products(self):
        """Background sync products with progress"""
        try:
            print("\n" + "="*60)
            print("PRODUCT SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("PRODUCTS", 1, 1)
            self._sync_products_data(client)
            
            print("PRODUCT SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Product sync error: {e}")
    
    def _background_sync_orders(self):
        """Background sync orders with progress"""
        try:
            print("\n" + "="*60)
            print("ORDER SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("ORDERS", 1, 1)
            self._sync_orders_data(client)
            
            print("ORDER SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Order sync error: {e}")
    
    def _background_sync_inventory(self):
        """Background sync inventory with progress"""
        try:
            print("\n" + "="*60)
            print("INVENTORY SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("INVENTORY", 1, 1)
            self._sync_inventory_data(client)
            
            print("INVENTORY SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Inventory sync error: {e}")
    
    def _background_sync_shipping(self):
        """Background sync shipping with progress"""
        try:
            print("\n" + "="*60)
            print("SHIPPING SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("SHIPPING", 1, 1)
            self._sync_shipping_data(client)
            
            print("SHIPPING SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Shipping sync error: {e}")
    
    # Data sync implementations
    def _sync_customers_data(self, client):
        """Sync customer data with proper field mapping"""
        from customers.models import ShopifyCustomer, ShopifyCustomerAddress
        from django.utils.dateparse import parse_datetime
        from datetime import datetime
        
        print("Fetching customers from Shopify API...")
        customers_data = client.fetch_all_customers()
        print(f"Retrieved {len(customers_data)} customers from Shopify")
        print("Saving to database...")
        
        created_count = 0
        updated_count = 0
        address_count = 0
        
        for customer_data in customers_data:
            try:
                # Parse timestamps
                created_at = parse_datetime(customer_data.get('createdAt')) if customer_data.get('createdAt') else datetime.now()
                updated_at = parse_datetime(customer_data.get('updatedAt')) if customer_data.get('updatedAt') else datetime.now()
                
                # Create or update customer with proper field mapping
                customer, created = ShopifyCustomer.objects.update_or_create(
                    shopify_id=customer_data['id'],
                    defaults={
                        'email': customer_data.get('email') or '',
                        'first_name': customer_data.get('firstName') or 'N/A',
                        'last_name': customer_data.get('lastName') or 'N/A',
                        'phone': customer_data.get('phone') or '',
                        'state': customer_data.get('state', 'ENABLED'),
                        'verified_email': customer_data.get('verifiedEmail', False),
                        'tax_exempt': customer_data.get('taxExempt', False),
                        'number_of_orders': customer_data.get('numberOfOrders', 0),
                        'tags': customer_data.get('tags', []),
                        'accepts_marketing': customer_data.get('acceptsMarketing', False),
                        'marketing_opt_in_level': customer_data.get('marketingOptInLevel') or '',
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'store_domain': '7fa66c-ac.myshopify.com'
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Save addresses with correct field mapping
                if 'addresses' in customer_data:
                    for address_data in customer_data['addresses']:
                        ShopifyCustomerAddress.objects.update_or_create(
                            customer=customer,
                            shopify_id=address_data.get('id'),
                            defaults={
                                'first_name': address_data.get('firstName') or '',
                                'last_name': address_data.get('lastName') or '',
                                'company': address_data.get('company') or '',
                                'address1': address_data.get('address1') or '',
                                'address2': address_data.get('address2') or '',
                                'city': address_data.get('city') or '',
                                'province': address_data.get('province') or '',
                                'country': address_data.get('country') or '',
                                'zip_code': address_data.get('zip') or '',  # zip -> zip_code
                                'phone': address_data.get('phone') or '',
                                'is_default': address_data.get('default', False),
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        address_count += 1
                        
            except Exception as e:
                print(f"Error syncing customer {customer_data.get('id')}: {e}")
        
        print(f"Successfully synced customers")
        print(f"Created: {created_count}, Updated: {updated_count}, Addresses: {address_count}")
    
    def _sync_products_data(self, client):
        """Sync product data with proper field mapping"""
        from products.models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage
        from django.utils.dateparse import parse_datetime
        from datetime import datetime
        
        print("Fetching products from Shopify API...")
        products_data = client.fetch_all_products()
        print(f"Retrieved {len(products_data)} products from Shopify")
        print("Saving to database...")
        
        created_count = 0
        updated_count = 0
        variant_count = 0
        image_count = 0
        
        for product_data in products_data:
            try:
                # Parse timestamps
                created_at = parse_datetime(product_data.get('createdAt')) if product_data.get('createdAt') else datetime.now()
                updated_at = parse_datetime(product_data.get('updatedAt')) if product_data.get('updatedAt') else datetime.now()
                published_at = parse_datetime(product_data.get('publishedAt')) if product_data.get('publishedAt') else None
                
                # Create or update product with proper field mapping
                product, created = ShopifyProduct.objects.update_or_create(
                    shopify_id=product_data['id'],
                    defaults={
                        'title': product_data.get('title', ''),
                        'description': product_data.get('description', ''),
                        'vendor': product_data.get('vendor', ''),
                        'product_type': product_data.get('productType', ''),
                        'handle': product_data.get('handle', ''),
                        'status': product_data.get('status', 'ACTIVE'),
                        'published_at': published_at,
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'tags': product_data.get('tags', []),
                        'store_domain': '7fa66c-ac.myshopify.com'
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Save variants (using edges structure)
                if 'variants' in product_data:
                    variants_data = product_data['variants']
                    # Handle both edges and nodes structure
                    if 'edges' in variants_data:
                        variant_list = [edge['node'] for edge in variants_data['edges']]
                    elif 'nodes' in variants_data:
                        variant_list = variants_data['nodes']
                    else:
                        variant_list = []
                    
                    for idx, variant_data in enumerate(variant_list, 1):
                        variant, v_created = ShopifyProductVariant.objects.update_or_create(
                            product=product,
                            shopify_id=variant_data.get('id'),
                            defaults={
                                'title': variant_data.get('title', 'Default Title'),
                                'price': variant_data.get('price', '0.00'),
                                'sku': variant_data.get('sku') or '',  # Handle None SKUs
                                'position': idx,
                                'inventory_policy': variant_data.get('inventoryPolicy', 'DENY'),
                                'compare_at_price': variant_data.get('compareAtPrice'),
                                'barcode': variant_data.get('barcode', ''),
                                'created_at': created_at,
                                'updated_at': updated_at,
                                'taxable': variant_data.get('taxable', True),
                                'weight': float(variant_data.get('weight', 0.0)),
                                'weight_unit': variant_data.get('weightUnit', 'KILOGRAMS'),
                                'requires_shipping': variant_data.get('requiresShipping', True),
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        variant_count += 1
                        
                        # Link inventory item to variant
                        if 'inventoryItem' in variant_data and variant_data['inventoryItem']:
                            inventory_item_id = variant_data['inventoryItem'].get('id')
                            if inventory_item_id:
                                from inventory.models import ShopifyInventoryItem
                                try:
                                    inv_item = ShopifyInventoryItem.objects.get(shopify_id=inventory_item_id)
                                    inv_item.variant = variant
                                    inv_item.save(update_fields=['variant'])
                                except ShopifyInventoryItem.DoesNotExist:
                                    pass
                
                # Save images (using edges structure)
                if 'images' in product_data:
                    images_data = product_data['images']
                    # Handle both edges and nodes structure
                    if 'edges' in images_data:
                        image_list = [edge['node'] for edge in images_data['edges']]
                    elif 'nodes' in images_data:
                        image_list = images_data['nodes']
                    else:
                        image_list = []
                    
                    for image_data in image_list:
                        ShopifyProductImage.objects.update_or_create(
                            shopify_id=image_data.get('id'),
                            defaults={
                                'product': product,
                                'src': image_data.get('src', ''),
                                'alt_text': image_data.get('altText', ''),
                                'width': image_data.get('width', 0),
                                'height': image_data.get('height', 0),
                                'created_at': created_at,
                                'updated_at': updated_at,
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        image_count += 1
                        
            except Exception as e:
                print(f"Error syncing product {product_data.get('id')}: {e}")
        
        print(f"Successfully synced products")
        print(f"Created: {created_count}, Updated: {updated_count}")
        print(f"Variants: {variant_count}, Images: {image_count}")
    
    def _sync_orders_data(self, client):
        """Sync order data with proper field mapping"""
        from orders.models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress
        from django.utils.dateparse import parse_datetime
        from datetime import datetime
        
        print("Fetching orders from Shopify API...")
        orders_data = client.fetch_all_orders()
        print(f"Retrieved {len(orders_data)} orders from Shopify")
        print("Saving to database...")
        
        created_count = 0
        updated_count = 0
        line_items_count = 0
        
        for order_data in orders_data:
            try:
                # Parse timestamps
                created_at = parse_datetime(order_data.get('createdAt')) if order_data.get('createdAt') else datetime.now()
                updated_at = parse_datetime(order_data.get('updatedAt')) if order_data.get('updatedAt') else datetime.now()
                processed_at = parse_datetime(order_data.get('processedAt')) if order_data.get('processedAt') else None
                cancelled_at = parse_datetime(order_data.get('cancelledAt')) if order_data.get('cancelledAt') else None
                
                # Get total price
                total_price_set = order_data.get('totalPriceSet', {})
                shop_money = total_price_set.get('shopMoney', {})
                total_price = float(shop_money.get('amount', 0.0))
                currency = shop_money.get('currencyCode', 'AUD')
                
                # Create or update order
                order, created = ShopifyOrder.objects.update_or_create(
                    shopify_id=order_data['id'],
                    defaults={
                        'customer_email': order_data.get('email') or '',
                        'name': order_data.get('name', ''),
                        'order_number': order_data.get('name', '#0').replace('#', '') if order_data.get('name') else '0',
                        'financial_status': order_data.get('displayFinancialStatus', 'pending').lower(),
                        'fulfillment_status': order_data.get('displayFulfillmentStatus', 'null').lower() if order_data.get('displayFulfillmentStatus') else 'null',
                        'total_price': str(total_price),
                        'subtotal_price': '0.00',
                        'total_tax': '0.00',
                        'total_shipping_price': '0.00',
                        'currency_code': currency,
                        'processed_at': processed_at,
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'store_domain': '7fa66c-ac.myshopify.com'
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Save line items
                line_items = order_data.get('lineItems', {})
                if isinstance(line_items, dict) and 'edges' in line_items:
                    for edge in line_items['edges']:
                        item_data = edge.get('node', {})
                        
                        variant_data = item_data.get('variant', {})
                        product_data = item_data.get('product', {})
                        
                        # Look up actual product and variant objects
                        from products.models import ShopifyProduct, ShopifyProductVariant
                        product_obj = None
                        variant_obj = None
                        
                        if product_data and product_data.get('id'):
                            try:
                                product_obj = ShopifyProduct.objects.get(shopify_id=product_data['id'])
                            except ShopifyProduct.DoesNotExist:
                                pass
                        
                        if variant_data and variant_data.get('id'):
                            try:
                                variant_obj = ShopifyProductVariant.objects.get(shopify_id=variant_data['id'])
                            except ShopifyProductVariant.DoesNotExist:
                                pass
                        
                        ShopifyOrderLineItem.objects.update_or_create(
                            order=order,
                            shopify_id=item_data.get('id'),
                            defaults={
                                'title': item_data.get('title', ''),
                                'quantity': item_data.get('quantity', 1),
                                'price': variant_data.get('price', '0.00') if variant_data else '0.00',
                                'sku': variant_data.get('sku', '') if variant_data else '',
                                'variant_title': variant_data.get('title', '') if variant_data else '',
                                'product': product_obj,
                                'variant': variant_obj,
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        line_items_count += 1
                
                # Save shipping address
                shipping_addr = order_data.get('shippingAddress')
                if shipping_addr:
                    ShopifyOrderAddress.objects.update_or_create(
                        order=order,
                        address_type='shipping',
                        defaults={
                            'first_name': shipping_addr.get('firstName', ''),
                            'last_name': shipping_addr.get('lastName', ''),
                            'address1': shipping_addr.get('address1', ''),
                            'address2': shipping_addr.get('address2', ''),
                            'city': shipping_addr.get('city', ''),
                            'province': shipping_addr.get('province', ''),
                            'country': shipping_addr.get('country', ''),
                            'zip_code': shipping_addr.get('zip', ''),
                            'phone': shipping_addr.get('phone', ''),
                            'store_domain': '7fa66c-ac.myshopify.com'
                        }
                    )
                        
            except Exception as e:
                print(f"Error syncing order {order_data.get('id')}: {e}")
        
        print(f"Successfully synced orders")
        print(f"Created: {created_count}, Updated: {updated_count}, Line Items: {line_items_count}")
    
    def _sync_inventory_data(self, client):
        """Sync inventory data with proper field mapping"""
        from inventory.models import ShopifyInventoryItem, ShopifyInventoryLevel, ShopifyLocation
        from django.utils.dateparse import parse_datetime
        from datetime import datetime
        
        print("Fetching inventory data from Shopify API...")
        inventory_data = client.fetch_all_inventory_items()
        print(f"Retrieved {len(inventory_data)} inventory items from Shopify")
        print("Saving to database...")
        
        created_count = 0
        updated_count = 0
        level_count = 0
        location_count = 0
        
        for item_data in inventory_data:
            try:
                # Parse timestamps
                created_at = parse_datetime(item_data.get('createdAt')) if item_data.get('createdAt') else datetime.now()
                updated_at = parse_datetime(item_data.get('updatedAt')) if item_data.get('updatedAt') else datetime.now()
                
                # Create or update inventory item
                item, created = ShopifyInventoryItem.objects.update_or_create(
                    shopify_id=item_data['id'],
                    defaults={
                        'sku': item_data.get('sku', ''),
                        'tracked': item_data.get('tracked', False),
                        'requires_shipping': item_data.get('requiresShipping', True),
                        'cost': item_data.get('unitCost', {}).get('amount', '0.00') if item_data.get('unitCost') else '0.00',
                        'created_at': created_at,
                        'updated_at': updated_at,
                        'store_domain': '7fa66c-ac.myshopify.com'
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Process inventory levels and locations
                if 'inventoryLevels' in item_data and 'edges' in item_data['inventoryLevels']:
                    for edge in item_data['inventoryLevels']['edges']:
                        level_data = edge['node']
                        location_data = level_data.get('location', {})
                        
                        if location_data and location_data.get('id'):
                            # Create or update location
                            location, loc_created = ShopifyLocation.objects.get_or_create(
                                shopify_id=location_data['id'],
                                defaults={
                                    'name': location_data.get('name', ''),
                                    'active': True,
                                    'created_at': datetime.now(),
                                    'updated_at': datetime.now(),
                                    'store_domain': '7fa66c-ac.myshopify.com'
                                }
                            )
                            if loc_created:
                                location_count += 1
                            
                            # Create or update inventory level
                            level_updated_at = parse_datetime(level_data.get('updatedAt')) if level_data.get('updatedAt') else datetime.now()
                            
                            # Extract available quantity from quantities array
                            available = 0
                            quantities = level_data.get('quantities', [])
                            for qty in quantities:
                                if qty.get('name') == 'available':
                                    available = qty.get('quantity', 0)
                                    break
                            
                            ShopifyInventoryLevel.objects.update_or_create(
                                inventory_item=item,
                                location=location,
                                defaults={
                                    'available': available,
                                    'updated_at': level_updated_at,
                                    'store_domain': '7fa66c-ac.myshopify.com'
                                }
                            )
                            level_count += 1
                        
            except Exception as e:
                print(f"Error syncing inventory item {item_data.get('id')}: {e}")
        
        print(f"Successfully synced inventory")
        print(f"Created: {created_count}, Updated: {updated_count}")
        print(f"Locations: {location_count}, Levels: {level_count}")
    
    def _sync_shipping_data(self, client):
        """Sync shipping data with proper field mapping"""
        from shipping.models import ShopifyCarrierService, ShopifyDeliveryProfile, ShopifyDeliveryZone, ShopifyDeliveryMethod
        from django.utils.dateparse import parse_datetime
        from datetime import datetime
        
        print("Fetching shipping configuration from Shopify API...")
        
        carrier_count = 0
        profile_count = 0
        zone_count = 0
        method_count = 0
        
        # Fetch carrier services (try both queries)
        try:
            # First try carrierServices (custom/external services)
            carrier_query = """
            query {
                carrierServices(first: 50) {
                    edges {
                        node {
                            id
                            name
                            active
                            formattedName
                            supportsServiceDiscovery
                        }
                    }
                }
            }
            """
            response = client.execute_graphql_query(carrier_query)
            
            if 'data' in response and 'carrierServices' in response['data']:
                carriers_data = response['data']['carrierServices']
                if 'edges' in carriers_data:
                    for edge in carriers_data['edges']:
                        carrier_data = edge['node']
                        
                        ShopifyCarrierService.objects.update_or_create(
                            shopify_id=carrier_data['id'],
                            defaults={
                                'name': carrier_data.get('name', ''),
                                'active': carrier_data.get('active', True),
                                'service_discovery': carrier_data.get('supportsServiceDiscovery', False),
                                'carrier_service_type': 'api',
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        carrier_count += 1
            
            # If no carriers found, try availableCarrierServices (includes built-in services)
            if carrier_count == 0:
                print("No custom carriers found, trying availableCarrierServices...")
                available_query = """
                query {
                    availableCarrierServices {
                        carrierService {
                            id
                            name
                            active
                            supportsServiceDiscovery
                            callbackUrl
                        }
                    }
                }
                """
                response = client.execute_graphql_query(available_query)
                
                if 'data' in response and 'availableCarrierServices' in response['data']:
                    available_services = response['data']['availableCarrierServices']
                    for item in available_services:
                        carrier_data = item.get('carrierService')
                        if carrier_data:
                            ShopifyCarrierService.objects.update_or_create(
                                shopify_id=carrier_data['id'],
                                defaults={
                                    'name': carrier_data.get('name', ''),
                                    'active': carrier_data.get('active', True),
                                    'service_discovery': carrier_data.get('supportsServiceDiscovery', False),
                                    'carrier_service_type': 'legacy',
                                    'callback_url': carrier_data.get('callbackUrl') or '',
                                    'store_domain': '7fa66c-ac.myshopify.com'
                                }
                            )
                            carrier_count += 1
                        
            print(f"Synced {carrier_count} carrier services")
        except Exception as e:
            print(f"Error syncing carrier services: {e}")
        
        # Fetch delivery profiles with zones and methods (one profile at a time to avoid cost limit)
        try:
            # First get profile IDs
            profile_list_query = """
            query {
                deliveryProfiles(first: 50) {
                    edges {
                        node {
                            id
                            name
                            default
                        }
                    }
                }
            }
            """
            response = client.execute_graphql_query(profile_list_query)
            
            if 'data' in response and 'deliveryProfiles' in response['data']:
                profiles_data = response['data']['deliveryProfiles']
                if 'edges' in profiles_data:
                    for edge in profiles_data['edges']:
                        profile_data = edge['node']
                        
                        # Create profile
                        profile, created = ShopifyDeliveryProfile.objects.update_or_create(
                            shopify_id=profile_data['id'],
                            defaults={
                                'name': profile_data.get('name', ''),
                                'default': profile_data.get('default', False),
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        profile_count += 1
                        
                        # Now fetch zones and methods for this profile
                        try:
                            profile_id = profile_data['id'].split('/')[-1]
                            zones_query = f"""
                            query {{
                                deliveryProfile(id: "{profile_data['id']}") {{
                                    profileLocationGroups {{
                                        locationGroupZones(first: 20) {{
                                            edges {{
                                                node {{
                                                    zone {{
                                                        id
                                                        name
                                                        countries {{
                                                            code {{
                                                                countryCode
                                                            }}
                                                        }}
                                                    }}
                                                    methodDefinitions(first: 20) {{
                                                        edges {{
                                                            node {{
                                                                id
                                                                active
                                                                description
                                                            }}
                                                        }}
                                                    }}
                                                }}
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                            """
                            zones_response = client.execute_graphql_query(zones_query)
                            
                            if 'data' in zones_response and 'deliveryProfile' in zones_response['data']:
                                profile_detail = zones_response['data']['deliveryProfile']
                                if profile_detail:
                                    for location_group in profile_detail.get('profileLocationGroups', []):
                                        zones_data = location_group.get('locationGroupZones', {})
                                        if 'edges' in zones_data:
                                            for zone_edge in zones_data['edges']:
                                                zone_node = zone_edge['node']
                                                zone_data = zone_node.get('zone', {})
                                                
                                                # Extract countries
                                                countries = []
                                                for country in zone_data.get('countries', []):
                                                    code_data = country.get('code', {})
                                                    if code_data.get('countryCode'):
                                                        countries.append({'countryCode': code_data['countryCode']})
                                                
                                                # Create zone
                                                zone, z_created = ShopifyDeliveryZone.objects.update_or_create(
                                                    shopify_id=zone_data['id'],
                                                    defaults={
                                                        'profile': profile,
                                                        'name': zone_data.get('name', ''),
                                                        'countries': countries,
                                                        'store_domain': '7fa66c-ac.myshopify.com'
                                                    }
                                                )
                                                zone_count += 1
                                                
                                                # Process methods
                                                methods_data = zone_node.get('methodDefinitions', {})
                                                if 'edges' in methods_data:
                                                    for method_edge in methods_data['edges']:
                                                        method_data = method_edge['node']
                                                        
                                                        # Generate name from ID since API doesn't provide one
                                                        method_id = method_data['id'].split('/')[-1]
                                                        method_name = f"Method {method_id}"
                                                        
                                                        ShopifyDeliveryMethod.objects.update_or_create(
                                                            shopify_id=method_data['id'],
                                                            defaults={
                                                                'zone': zone,
                                                                'name': method_name,
                                                                'method_type': 'shipping',
                                                                'store_domain': '7fa66c-ac.myshopify.com'
                                                            }
                                                        )
                                                        method_count += 1
                        except Exception as e:
                            print(f"Error fetching zones for profile {profile_data.get('name')}: {e}")
                        
            print(f"Synced {profile_count} profiles, {zone_count} zones, {method_count} methods")
        except Exception as e:
            print(f"Error syncing delivery profiles: {e}")
        
        print(f"Shipping sync completed: {carrier_count} carriers, {profile_count} profiles, {zone_count} zones, {method_count} methods")
    
    def _background_sync_payments(self):
        """Background sync payments with progress"""
        try:
            print("\n" + "="*60)
            print("PAYMENTS SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("PAYMENTS", 1, 1)
            self._sync_payments_data(client)
            
            print("PAYMENTS SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Payments sync error: {e}")
    
    def _sync_payments_data(self, client):
        """Sync Shopify Payments data"""
        from payments.models import (
            ShopifyPaymentsAccount,
            ShopifyBalanceTransaction,
            ShopifyPayout,
            ShopifyDispute,
            ShopifyFinanceKYC
        )
        from payments.shopify_payments_client import ShopifyPaymentsClient
        from django.utils.dateparse import parse_datetime
        
        print("Fetching Shopify Payments data from API...")
        
        payments_client = ShopifyPaymentsClient()
        account_count = 0
        transaction_count = 0
        payout_count = 0
        dispute_count = 0
        kyc_count = 0
        
        try:
            # Fetch account info
            print("Fetching payments account info...")
            account_response = payments_client.fetch_account_info()
            
            if 'data' in account_response and 'shopifyPaymentsAccount' in account_response['data']:
                account_data = account_response['data']['shopifyPaymentsAccount']
                if account_data:
                    account, created = ShopifyPaymentsAccount.objects.update_or_create(
                        shopify_id=account_data['id'],
                        defaults={
                            'account_opener_name': account_data.get('accountOpenerName', ''),
                            'activated': account_data.get('activated', False),
                            'country': account_data.get('country', ''),
                            'default_currency': account_data.get('defaultCurrency', ''),
                            'onboardable': account_data.get('onboardable', False),
                            'payout_statement_descriptor': account_data.get('payoutStatementDescriptor', ''),
                            'charge_statement_descriptor': account_data.get('chargeStatementDescriptor', ''),
                            'store_domain': '7fa66c-ac.myshopify.com'
                        }
                    )
                    account_count = 1
                    print(f"✓ Synced payments account: {account.country} ({account.default_currency})")
                    
                    # Fetch KYC info
                    try:
                        print("Fetching KYC information...")
                        kyc_response = payments_client.fetch_finance_kyc_info()
                        
                        if 'data' in kyc_response and 'financeKycInformation' in kyc_response['data']:
                            kyc_data = kyc_response['data']['financeKycInformation']
                            if kyc_data:
                                business_address = kyc_data.get('businessAddress', {})
                                industry = kyc_data.get('industry', {})
                                shop_owner = kyc_data.get('shopOwner', {})
                                tax_id = kyc_data.get('taxIdentification', {})
                                
                                ShopifyFinanceKYC.objects.update_or_create(
                                    account=account,
                                    defaults={
                                        'legal_name': kyc_data.get('legalName', ''),
                                        'business_type': kyc_data.get('businessType', '').lower(),
                                        'address_line1': business_address.get('addressLine1', ''),
                                        'address_line2': business_address.get('addressLine2', ''),
                                        'city': business_address.get('city', ''),
                                        'zone': business_address.get('zone', ''),
                                        'postal_code': business_address.get('postalCode', ''),
                                        'country': business_address.get('country', ''),
                                        'industry_category': industry.get('category', ''),
                                        'industry_category_label': industry.get('categoryLabel', ''),
                                        'industry_code': industry.get('code'),
                                        'industry_subcategory_label': industry.get('subcategoryLabel', ''),
                                        'owner_email': shop_owner.get('email', ''),
                                        'owner_first_name': shop_owner.get('firstName', ''),
                                        'owner_last_name': shop_owner.get('lastName', ''),
                                        'owner_phone': shop_owner.get('phone', ''),
                                        'tax_id_type': tax_id.get('taxIdentificationType', '').lower() if tax_id else '',
                                        'tax_id_value': tax_id.get('value', '') if tax_id else '',
                                        'store_domain': '7fa66c-ac.myshopify.com'
                                    }
                                )
                                kyc_count = 1
                                print(f"✓ Synced KYC information")
                    except Exception as e:
                        print(f"⚠ KYC info not available: {e}")
                    
                    # Fetch balance transactions
                    print("Fetching balance transactions...")
                    transactions = payments_client.fetch_all_balance_transactions()
                    for txn in transactions:
                        ShopifyBalanceTransaction.objects.update_or_create(
                            shopify_id=txn['id'],
                            defaults={
                                'account': account,
                                'transaction_type': txn.get('type', '').lower(),
                                'test': txn.get('test', False),
                                'amount': txn['amount']['amount'],
                                'currency_code': txn['amount']['currencyCode'],
                                'fee_amount': txn.get('fee', {}).get('amount', 0),
                                'net_amount': txn.get('net', {}).get('amount', 0),
                                'source_id': txn.get('sourceId', ''),
                                'source_type': txn.get('sourceType', '').lower() if txn.get('sourceType') else '',
                                'source_order_transaction_id': txn.get('sourceOrderTransactionId', ''),
                                'associated_order_id': txn.get('associatedOrder', {}).get('id', '') if txn.get('associatedOrder') else '',
                                'associated_payout_id': txn.get('associatedPayout', {}).get('id', '') if txn.get('associatedPayout') else '',
                                'associated_payout_status': txn.get('associatedPayout', {}).get('status', '') if txn.get('associatedPayout') else '',
                                'adjustment_reason': txn.get('adjustmentReason', ''),
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        transaction_count += 1
                    print(f"✓ Synced {transaction_count} balance transactions")
                    
                    # Fetch payouts
                    print("Fetching payouts...")
                    payouts = payments_client.fetch_all_payouts()
                    for payout in payouts:
                        ShopifyPayout.objects.update_or_create(
                            shopify_id=payout['id'],
                            defaults={
                                'account': account,
                                'status': payout.get('status', '').lower(),
                                'amount': payout.get('gross', {}).get('amount', 0) if payout.get('gross') else 0,
                                'currency_code': payout.get('gross', {}).get('currencyCode', '') if payout.get('gross') else '',
                                'bank_account_id': payout.get('bankAccount', {}).get('id', '') if payout.get('bankAccount') else '',
                                'payout_date': parse_datetime(payout['issuedAt']) if payout.get('issuedAt') else None,
                                'store_domain': '7fa66c-ac.myshopify.com'
                            }
                        )
                        payout_count += 1
                    print(f"✓ Synced {payout_count} payouts")
                    
                    # Fetch disputes
                    print("Fetching disputes...")
                    disputes_response = payments_client.fetch_disputes(first=100)
                    if 'data' in disputes_response and 'shopifyPaymentsAccount' in disputes_response['data']:
                        account_data = disputes_response['data']['shopifyPaymentsAccount']
                        if account_data and 'disputes' in account_data:
                            for edge in account_data['disputes'].get('edges', []):
                                dispute = edge['node']
                                reason_details = dispute.get('reasonDetails', {})
                                
                                ShopifyDispute.objects.update_or_create(
                                    shopify_id=dispute['id'],
                                    defaults={
                                        'account': account,
                                        'status': dispute.get('status', '').lower(),
                                        'dispute_type': dispute.get('type', 'chargeback').lower(),
                                        'reason': reason_details.get('reason', '').lower() if reason_details else '',
                                        'network_reason_code': reason_details.get('networkReasonCode', '') if reason_details else '',
                                        'amount': dispute['amount']['amount'],
                                        'currency_code': dispute['amount']['currencyCode'],
                                        'order_id': dispute.get('order', {}).get('id', '') if dispute.get('order') else '',
                                        'initiated_at': parse_datetime(dispute['initiatedAt']) if dispute.get('initiatedAt') else None,
                                        'evidence_due_by': parse_datetime(dispute['evidenceDueBy']) if dispute.get('evidenceDueBy') else None,
                                        'evidence_sent_on': parse_datetime(dispute['evidenceSentOn']) if dispute.get('evidenceSentOn') else None,
                                        'finalized_on': parse_datetime(dispute['finalizedOn']) if dispute.get('finalizedOn') else None,
                                        'store_domain': '7fa66c-ac.myshopify.com'
                                    }
                                )
                                dispute_count += 1
                    print(f"✓ Synced {dispute_count} disputes")
                    
        except Exception as e:
            print(f"❌ Error syncing payments data: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\nPayments sync completed:")
        print(f"  Accounts: {account_count}")
        print(f"  Transactions: {transaction_count}")
        print(f"  Payouts: {payout_count}")
        print(f"  Disputes: {dispute_count}")
        print(f"  KYC Info: {kyc_count}")
    
    def _background_sync_webhooks(self):
        """Background sync webhook subscriptions with progress"""
        try:
            print("\n" + "="*60)
            print("WEBHOOK SUBSCRIPTIONS SYNC INITIATED")
            print("="*60)
            
            client = EnhancedShopifyAPIClient()
            self._show_progress("WEBHOOKS", 1, 1)
            self._sync_webhooks_data(client)
            
            print("WEBHOOK SUBSCRIPTIONS SYNC COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"Webhook subscriptions sync error: {e}")
    
    def _sync_webhooks_data(self, client):
        """Sync webhook subscriptions data"""
        from subscriptions.models import ShopifyWebhookSubscription, ShopifyWebhookSyncLog
        from subscriptions.shopify_webhooks_client import ShopifyWebhooksClient
        
        print("Fetching webhook subscriptions from Shopify API...")
        
        webhooks_client = ShopifyWebhooksClient()
        subscription_count = 0
        created_count = 0
        updated_count = 0
        
        try:
            # Fetch all webhook subscriptions
            print("Fetching all webhook subscriptions...")
            subscriptions = webhooks_client.fetch_all_webhook_subscriptions()
            
            for sub in subscriptions:
                endpoint = sub.get('endpoint', {})
                endpoint_type_name = endpoint.get('__typename', 'Unknown')
                
                # Determine endpoint type and URI
                if endpoint_type_name == 'WebhookHttpEndpoint':
                    endpoint_type = 'http'
                    uri = endpoint.get('callbackUrl', '')
                elif endpoint_type_name == 'WebhookEventBridgeEndpoint':
                    endpoint_type = 'eventbridge'
                    uri = endpoint.get('arn', '')
                elif endpoint_type_name == 'WebhookPubSubEndpoint':
                    endpoint_type = 'pubsub'
                    uri = f"{endpoint.get('pubSubProject', '')}/{endpoint.get('pubSubTopic', '')}"
                else:
                    endpoint_type = 'http'
                    uri = ''
                
                # Convert topic from SCREAMING_SNAKE_CASE to snake/case format for choices
                topic = sub.get('topic', '').lower().replace('_', '/')
                if '/' not in topic:
                    topic = 'other'
                
                # Get API version
                api_version_data = sub.get('apiVersion', {})
                api_version = api_version_data.get('handle', '') if api_version_data else ''
                
                subscription_obj, created = ShopifyWebhookSubscription.objects.update_or_create(
                    shopify_id=sub['id'],
                    defaults={
                        'legacy_resource_id': sub.get('legacyResourceId'),
                        'topic': topic,
                        'format': sub.get('format', 'JSON').lower(),
                        'endpoint_type': endpoint_type,
                        'uri': uri,
                        'api_version': api_version,
                        'filter_query': sub.get('filter', ''),
                        'include_fields': sub.get('includeFields', []),
                        'metafield_namespaces': sub.get('metafieldNamespaces', []),
                        'is_active': True,
                        'store_domain': '7fa66c-ac.myshopify.com'
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                subscription_count += 1
            
            print(f"✓ Synced {subscription_count} webhook subscriptions")
            print(f"  Created: {created_count}")
            print(f"  Updated: {updated_count}")
            
        except Exception as e:
            print(f"❌ Error syncing webhook subscriptions: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\nWebhook subscriptions sync completed:")
        print(f"  Total: {subscription_count}")
        print(f"  Created: {created_count}")
        print(f"  Updated: {updated_count}")


# Import models
from .models import ShopifyStore, WebhookEndpoint, SyncOperation, APIRateLimit

# Register existing models
@admin.register(ShopifyStore)
class ShopifyStoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'store_domain', 'is_active', 'last_sync', 'created_at')
    list_filter = ('is_active', 'currency', 'country_code')
    search_fields = ('store_name', 'store_domain')
    readonly_fields = ('created_at', 'updated_at', 'last_sync')

@admin.register(SyncOperation)
class SyncOperationAdmin(admin.ModelAdmin):
    list_display = ('store', 'operation_type', 'status', 'progress_display', 'started_at', 'completed_at')
    list_filter = ('operation_type', 'status', 'started_at')
    search_fields = ('store__store_name', 'operation_type')
    readonly_fields = ('created_at', 'updated_at', 'progress_percentage')
    
    def progress_display(self, obj):
        return f"{obj.processed_records}/{obj.total_records} ({obj.progress_percentage:.1f}%)"
    progress_display.short_description = "Progress"

@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ('store', 'topic', 'address', 'is_active', 'format')
    list_filter = ('is_active', 'format', 'topic')
    search_fields = ('topic', 'address')

@admin.register(APIRateLimit)
class APIRateLimitAdmin(admin.ModelAdmin):
    list_display = ('store', 'api_type', 'usage_display', 'is_throttled', 'updated_at')
    list_filter = ('api_type', 'is_throttled')
    readonly_fields = ('usage_percentage',)
    
    def usage_display(self, obj):
        return f"{obj.current_calls}/{obj.max_calls} ({obj.usage_percentage:.1f}%)"
    usage_display.short_description = "Usage"

# Create a separate model for the sync dashboard
class ShopifyIntegrationDashboard(models.Model):
    """Dummy model for sync dashboard admin"""
    name = models.CharField(max_length=100, default="Sync Dashboard")
    
    class Meta:
        app_label = 'shopify_integration'
        verbose_name = 'Sync Dashboard'
        verbose_name_plural = 'Sync Dashboard'
        managed = False  # Don't create database table
    
    def __str__(self):
        return "Shopify Sync Dashboard"

# Register the sync dashboard
admin.site.register(ShopifyIntegrationDashboard, ShopifyIntegrationAdminView)
