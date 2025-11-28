"""
Core Admin Configuration
Provides a central dashboard for all Shopify store management
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from customers.realtime_sync import get_customer_sync_stats
from products.realtime_sync import get_product_sync_stats
from orders.realtime_sync import get_order_sync_stats
from inventory.realtime_sync import get_inventory_sync_stats


class LavishLibraryAdminSite(AdminSite):
    """
    Custom admin site for Lavish Library Shopify integration
    """
    site_header = "Lavish Library - Shopify Store Management"
    site_title = "Lavish Library Admin"
    index_title = "Welcome to Lavish Library Store Management"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """
        Custom dashboard view with store statistics
        """
        context = {
            'title': 'Store Dashboard',
            'site_title': self.site_title,
            'site_header': self.site_header,
            'has_permission': True,
        }
        
        try:
            # Get all sync statistics
            customer_stats = get_customer_sync_stats()
            product_stats = get_product_sync_stats()
            order_stats = get_order_sync_stats()
            inventory_stats = get_inventory_sync_stats()
            
            context.update({
                'customer_stats': customer_stats,
                'product_stats': product_stats,
                'order_stats': order_stats,
                'inventory_stats': inventory_stats,
                'store_domain': customer_stats.get('store_domain', 'Unknown'),
            })
            
        except Exception as e:
            messages.error(request, f"Error loading dashboard data: {e}")
            context.update({
                'error': str(e),
                'customer_stats': {},
                'product_stats': {},
                'order_stats': {},
                'inventory_stats': {},
            })
        
        return render(request, 'admin/dashboard.html', context)
    
    def index(self, request, extra_context=None):
        """
        Override the default admin index to show our custom dashboard
        """
        extra_context = extra_context or {}
        
        # Add dashboard link
        extra_context['dashboard_url'] = '/admin/dashboard/'
        extra_context['custom_dashboard'] = format_html(
            '<div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px;">'
            '<h2>🏪 Store Management Dashboard</h2>'
            '<p>Get real-time insights into your Shopify store data.</p>'
            '<a href="/admin/dashboard/" class="button default">📊 View Dashboard</a>'
            '</div>'
        )
        
        return super().index(request, extra_context)


# Create custom admin site instance
admin_site = LavishLibraryAdminSite(name='lavish_admin')


# Admin action to refresh all data
def refresh_all_store_data(modeladmin, request, queryset):
    """
    Admin action to refresh all store data from Shopify
    """
    try:
        from customers.realtime_sync import sync_customers_realtime
        from products.realtime_sync import sync_products_realtime
        from orders.realtime_sync import sync_orders_realtime
        
        # Sync all data types (with limits for safety)
        customer_result = sync_customers_realtime(limit=50)
        product_result = sync_products_realtime(limit=25)
        order_result = sync_orders_realtime(limit=25)
        
        messages.success(request, 
            f"✅ Store refresh completed! "
            f"Customers: {customer_result.get('stats', {}).get('total', 0)}, "
            f"Products: {product_result.get('stats', {}).get('total', 0)}, "
            f"Orders: {order_result.get('stats', {}).get('total', 0)}"
        )
        
    except Exception as e:
        messages.error(request, f"❌ Store refresh failed: {str(e)}")

refresh_all_store_data.short_description = "🔄 Refresh all store data from Shopify"
