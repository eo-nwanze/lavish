"""
API URL Configuration
Routes for exposing Django backend data to Shopify theme
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
]
