from django.urls import path
from . import views

app_name = 'shipping'

urlpatterns = [
    # Carrier services
    path('carriers/', views.carrier_service_list, name='carrier_service_list'),
    
    # Delivery profiles, zones, and methods
    path('delivery-profiles/', views.delivery_profiles_list, name='delivery_profiles_list'),
    
    # Fulfillment orders
    path('fulfillment-orders/', views.fulfillment_order_list, name='fulfillment_order_list'),
    
    # Shopify Carrier Service Callback (CSRF exempt for external webhook)
    path('calculate-rates/', views.calculate_shipping_rates, name='calculate_shipping_rates'),
    
    # Sync shipping data from Shopify
    path('sync/', views.sync_shipping_data, name='sync_shipping_data'),
    
    # Query available shipping rates
    path('rates/', views.shipping_rates_query, name='shipping_rates_query'),
    
    # Test endpoint
    path('test-rates/', views.test_shipping_rates, name='test_shipping_rates'),
]
