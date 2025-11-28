"""
API Views for Shopify Data
Exposes Django backend data to Shopify theme frontend
"""

from rest_framework import viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Sum
from products.models import ShopifyProduct
from inventory.models import ShopifyInventoryLevel
from customers.models import ShopifyCustomer
from orders.models import ShopifyOrder
from shipping.models import ShopifyCarrierService, ShopifyDeliveryMethod
from locations.models import Country, State, City
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    OrderSerializer, CustomerSerializer,
    CarrierServiceSerializer, DeliveryMethodSerializer,
    CountrySerializer, StateSerializer, CitySerializer
)


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for location data (countries, states, cities)
    
    Endpoints:
    - GET /api/locations/countries/ - List all countries
    - GET /api/locations/countries/{id}/ - Get country by ID
    - GET /api/locations/countries/{country_id}/states/ - Get states for a country
    - GET /api/locations/states/{state_id}/cities/ - Get cities for a state
    - GET /api/locations/phone-codes/ - Get phone codes for all countries
    """
    permission_classes = [AllowAny]
    queryset = Country.objects.all()
    
    @action(detail=False, methods=['get'])
    def countries(self, request):
        """Get all countries with their states and cities"""
        countries = Country.objects.prefetch_related('states__cities').all()
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='countries/(?P<country_id>[^/.]+)/states')
    def country_states(self, request, country_id=None):
        """Get states for a specific country"""
        try:
            country = Country.objects.get(id=country_id)
            states = country.states.prefetch_related('cities').all()
            serializer = StateSerializer(states, many=True)
            return Response(serializer.data)
        except Country.DoesNotExist:
            return Response({'error': 'Country not found'}, status=404)
    
    @action(detail=False, methods=['get'], url_path='states/(?P<state_id>[^/.]+)/cities')
    def state_cities(self, request, state_id=None):
        """Get cities for a specific state"""
        try:
            state = State.objects.get(id=state_id)
            cities = state.cities.all()
            serializer = CitySerializer(cities, many=True)
            return Response(serializer.data)
        except State.DoesNotExist:
            return Response({'error': 'State not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def phone_codes(self, request):
        """Get phone codes for all countries"""
        countries = Country.objects.all()
        phone_codes = [
            {
                'country_id': country.id,
                'country_name': country.name,
                'iso_code': country.iso_code,
                'phone_code': country.phone_code,
                'flag_emoji': country.flag_emoji
            }
            for country in countries
        ]
        return Response(phone_codes)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products
    
    Endpoints:
    - GET /api/products/ - List all products
    - GET /api/products/{id}/ - Get product by ID
    - GET /api/products/by-handle/{handle}/ - Get product by handle
    - GET /api/products/featured/ - Get featured products
    - GET /api/products/search/?q=query - Search products
    """
    queryset = ShopifyProduct.objects.filter(status='active').prefetch_related('images', 'variants')
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'product_type', 'vendor', 'tags']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'by_handle':
            return ProductDetailSerializer
        return ProductListSerializer
    
    @action(detail=False, methods=['get'], url_path='by-handle/(?P<handle>[^/.]+)')
    def by_handle(self, request, handle=None):
        """Get product by handle"""
        try:
            product = self.queryset.get(handle=handle)
            serializer = ProductDetailSerializer(product)
            return Response(serializer.data)
        except ShopifyProduct.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products (products with inventory)"""
        products = self.queryset.filter(
            variants__inventory_item__levels__available__gt=0
        ).distinct()[:12]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get products by type"""
        product_type = request.query_params.get('type', None)
        if product_type:
            products = self.queryset.filter(product_type__iexact=product_type)
            serializer = ProductListSerializer(products, many=True)
            return Response(serializer.data)
        return Response({'error': 'Type parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_vendor(self, request):
        """Get products by vendor"""
        vendor = request.query_params.get('vendor', None)
        if vendor:
            products = self.queryset.filter(vendor__iexact=vendor)
            serializer = ProductListSerializer(products, many=True)
            return Response(serializer.data)
        return Response({'error': 'Vendor parameter required'}, status=400)


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for inventory levels
    
    Endpoints:
    - GET /api/inventory/ - List all inventory levels
    - GET /api/inventory/low-stock/ - Get low stock items
    """
    queryset = ShopifyInventoryLevel.objects.select_related('inventory_item', 'location')
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get low stock items (available <= 10)"""
        threshold = int(request.query_params.get('threshold', 10))
        levels = self.queryset.filter(available__lte=threshold, available__gt=0)
        
        data = []
        for level in levels:
            if level.inventory_item.variant:
                data.append({
                    'product': level.inventory_item.variant.product.title,
                    'variant': level.inventory_item.variant.title,
                    'sku': level.inventory_item.sku,
                    'location': level.location.name,
                    'available': level.available
                })
        
        return Response(data)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for orders
    
    Endpoints:
    - GET /api/orders/ - List all orders
    - GET /api/orders/{id}/ - Get order by ID
    - GET /api/orders/recent/ - Get recent orders
    """
    queryset = ShopifyOrder.objects.prefetch_related('line_items', 'customer')
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent orders"""
        limit = int(request.query_params.get('limit', 10))
        orders = self.queryset.order_by('-created_at')[:limit]
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for customers
    
    Endpoints:
    - GET /api/customers/ - List all customers
    - GET /api/customers/{id}/ - Get customer by ID
    """
    queryset = ShopifyCustomer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]
    ordering = ['-created_at']


class ShippingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for shipping options
    
    Endpoints:
    - GET /api/shipping/carriers/ - List carrier services
    - GET /api/shipping/methods/ - List delivery methods
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def carriers(self, request):
        """Get active carrier services"""
        carriers = ShopifyCarrierService.objects.filter(active=True)
        serializer = CarrierServiceSerializer(carriers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def methods(self, request):
        """Get delivery methods"""
        methods = ShopifyDeliveryMethod.objects.select_related('zone')
        serializer = DeliveryMethodSerializer(methods, many=True)
        return Response(serializer.data)


class StatsView(generics.GenericAPIView):
    """
    API endpoint for store statistics
    
    Endpoint:
    - GET /api/stats/ - Get store statistics
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get store statistics"""
        stats = {
            'products': {
                'total': ShopifyProduct.objects.count(),
                'active': ShopifyProduct.objects.filter(status='active').count(),
            },
            'orders': {
                'total': ShopifyOrder.objects.count(),
                'pending': ShopifyOrder.objects.filter(financial_status='pending').count(),
                'fulfilled': ShopifyOrder.objects.filter(fulfillment_status='fulfilled').count(),
            },
            'customers': {
                'total': ShopifyCustomer.objects.count(),
            },
            'inventory': {
                'total_items': ShopifyInventoryLevel.objects.count(),
                'low_stock': ShopifyInventoryLevel.objects.filter(available__lte=10, available__gt=0).count(),
                'out_of_stock': ShopifyInventoryLevel.objects.filter(available=0).count(),
            }
        }
        
        return Response(stats)
