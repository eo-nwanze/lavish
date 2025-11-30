from django.urls import path
from . import views

app_name = 'shipping'

urlpatterns = [
    path('carriers/', views.carrier_service_list, name='carrier_service_list'),
    path('fulfillment-orders/', views.fulfillment_order_list, name='fulfillment_order_list'),
    
    # Shopify Carrier Service Callback
    path('calculate-rates/', views.calculate_shipping_rates, name='calculate_shipping_rates'),
    
    # Test endpoint
    path('test-rates/', views.test_shipping_rates, name='test_shipping_rates'),
]
