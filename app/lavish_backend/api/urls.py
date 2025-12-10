"""
API URL Configuration
Routes for exposing Django backend data to Shopify theme
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import frontend_views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'inventory', views.InventoryViewSet, basename='inventory')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'shipping', views.ShippingViewSet, basename='shipping')
router.register(r'locations', views.LocationViewSet, basename='location')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Stats endpoint
    path('stats/', views.StatsView.as_view(), name='stats'),
    
    # Frontend-specific API endpoints
    path('customers/profile/update/', frontend_views.update_customer_profile, name='customer_profile_update'),
    path('customers/addresses/create/', frontend_views.create_customer_address, name='customer_address_create'),
    path('customers/addresses/<int:address_id>/update/', frontend_views.update_customer_address, name='customer_address_update'),
    path('customers/addresses/<int:address_id>/delete/', frontend_views.delete_customer_address, name='customer_address_delete'),
    path('orders/customer-orders/', views.OrderViewSet.as_view({'get': 'customer_orders'}), name='customer_orders'),
    path('orders/<str:order_id>/update-address/', frontend_views.update_order_address, name='order_update_address'),
    path('orders/<str:order_id>/cancel/', frontend_views.cancel_order, name='order_cancel'),
    path('orders/<str:order_id>/invoice/', frontend_views.download_order_invoice, name='order_invoice'),
]
