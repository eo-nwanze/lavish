"""
API Views for Shopify Data
Exposes Django backend data to Shopify theme frontend
"""

from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from products.models import ShopifyProduct
from inventory.models import ShopifyInventoryLevel
from customers.models import ShopifyCustomer, ShopifyCustomerAddress
from orders.models import ShopifyOrder, ShopifyOrderAddress
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


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for orders with full CRUD operations
    
    Endpoints:
    - GET /api/orders/ - List all orders
    - GET /api/orders/{id}/ - Get order by ID
    - POST /api/orders/ - Create new order
    - PUT /api/orders/{id}/ - Update order
    - PATCH /api/orders/{id}/ - Partial update order
    - DELETE /api/orders/{id}/ - Delete order
    - GET /api/orders/customer-orders/ - Get orders for current customer
    - POST /api/orders/{id}/update-address/ - Update order shipping address
    - POST /api/orders/{id}/cancel/ - Cancel order
    - GET /api/orders/{id}/invoice/ - Download order invoice
    """
    queryset = ShopifyOrder.objects.prefetch_related('line_items', 'customer')
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def customer_orders(self, request):
        """Get orders for the current customer"""
        try:
            customer_email = request.GET.get('customer_email')
            if not customer_email:
                return Response(
                    {'error': 'Customer email required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            orders = ShopifyOrder.objects.filter(
                customer_email=customer_email
            ).order_by('-created_at')
            
            # Calculate statistics
            total_orders = orders.count()
            pending_orders = orders.filter(financial_status='pending').count()
            fulfilled_orders = orders.filter(fulfillment_status='fulfilled').count()
            total_spent = sum(order.total_price or 0 for order in orders)
            
            serializer = self.get_serializer(orders, many=True)
            
            return Response({
                'success': True,
                'orders': serializer.data,
                'statistics': {
                    'total_orders': total_orders,
                    'pending_orders': pending_orders,
                    'fulfilled_orders': fulfilled_orders,
                    'total_spent': float(total_spent)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_address(self, request, pk=None):
        """Update order shipping address"""
        try:
            order = self.get_object()
            
            # Get or create shipping address
            from orders.models import ShopifyOrderAddress
            shipping_address, created = ShopifyOrderAddress.objects.get_or_create(
                order=order,
                address_type='shipping',
                defaults={
                    'first_name': '',
                    'last_name': '',
                    'company': '',
                    'address1': '',
                    'address2': '',
                    'city': '',
                    'province': '',
                    'country': '',
                    'zip_code': '',
                    'phone': '',
                }
            )
            
            # Update shipping address fields
            address_data = request.data.get('address', {})
            
            if 'first_name' in address_data:
                shipping_address.first_name = address_data['first_name']
            if 'last_name' in address_data:
                shipping_address.last_name = address_data['last_name']
            if 'company' in address_data:
                shipping_address.company = address_data['company']
            if 'address1' in address_data:
                shipping_address.address1 = address_data['address1']
            if 'address2' in address_data:
                shipping_address.address2 = address_data['address2']
            if 'city' in address_data:
                shipping_address.city = address_data['city']
            if 'province' in address_data:
                shipping_address.province = address_data['province']
            if 'country' in address_data:
                shipping_address.country = address_data['country']
            if 'zip' in address_data:
                shipping_address.zip_code = address_data['zip']
            if 'phone' in address_data:
                shipping_address.phone = address_data['phone']
            
            shipping_address.save()
            
            return Response({
                'success': True,
                'message': 'Order shipping address updated successfully'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        try:
            order = self.get_object()
            
            # Check if order can be cancelled
            if order.financial_status in ['paid', 'fulfilled']:
                return Response(
                    {'error': 'Order cannot be cancelled in current status'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update order status
            order.financial_status = 'cancelled'
            order.cancelled_at = timezone.now()
            order.cancel_reason = request.data.get('reason', 'Customer requested cancellation')
            order.save()
            
            return Response({
                'success': True,
                'message': 'Order cancelled successfully'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        """Generate and download order invoice"""
        try:
            order = self.get_object()
            
            # Generate invoice PDF (simplified version)
            # In a real implementation, you would use a PDF library like ReportLab
            invoice_data = {
                'order_name': order.name,
                'customer_email': order.customer_email,
                'created_at': order.created_at,
                'total_price': float(order.total_price or 0),
                'financial_status': order.financial_status,
                'fulfillment_status': order.fulfillment_status
            }
            
            # For now, return JSON data instead of PDF
            return Response({
                'success': True,
                'invoice_data': invoice_data,
                'message': 'Invoice data retrieved successfully'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent orders"""
        limit = int(request.query_params.get('limit', 10))
        orders = self.queryset.order_by('-created_at')[:limit]
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for customers with full CRUD operations
    
    Endpoints:
    - GET /api/customers/ - List all customers
    - GET /api/customers/{id}/ - Get customer by ID
    - POST /api/customers/ - Create new customer
    - PUT /api/customers/{id}/ - Update customer
    - PATCH /api/customers/{id}/ - Partial update customer
    - DELETE /api/customers/{id}/ - Delete customer
    - POST /api/customers/profile/update/ - Update customer profile
    - POST /api/customers/addresses/create/ - Create address
    - PUT /api/customers/addresses/{id}/update/ - Update address
    - DELETE /api/customers/addresses/{id}/delete/ - Delete address
    """
    queryset = ShopifyCustomer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """Update customer profile information"""
        try:
            customer_id = request.data.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'Customer ID required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            customer = ShopifyCustomer.objects.get(shopify_id=customer_id)
            
            # Update customer fields
            if 'first_name' in request.data:
                customer.first_name = request.data['first_name']
            if 'last_name' in request.data:
                customer.last_name = request.data['last_name']
            if 'phone' in request.data:
                customer.phone = request.data['phone']
            if 'email' in request.data:
                customer.email = request.data['email']
            if 'accepts_marketing' in request.data:
                customer.accepts_marketing = request.data['accepts_marketing']
            
            customer.save()
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'customer': {
                    'shopify_id': customer.shopify_id,
                    'email': customer.email,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'phone': customer.phone,
                    'accepts_marketing': customer.accepts_marketing
                }
            })
            
        except ShopifyCustomer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_address(self, request):
        """Create new customer address"""
        try:
            customer_id = request.data.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'Customer ID required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            customer = ShopifyCustomer.objects.get(shopify_id=customer_id)
            
            # Create address
            address = ShopifyCustomerAddress.objects.create(
                customer=customer,
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
                company=request.data.get('company', ''),
                address1=request.data.get('address1', ''),
                address2=request.data.get('address2', ''),
                city=request.data.get('city', ''),
                province=request.data.get('province', ''),
                country=request.data.get('country', ''),
                zip_code=request.data.get('zip_code', ''),
                phone=request.data.get('phone', ''),
                is_default=request.data.get('is_default', False)
            )
            
            return Response({
                'success': True,
                'message': 'Address created successfully',
                'address_id': address.id,
                'shopify_id': address.shopify_id
            })
            
        except ShopifyCustomer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['put', 'patch'])
    def update_address(self, request, pk=None):
        """Update customer address"""
        try:
            address = ShopifyCustomerAddress.objects.get(pk=pk)
            
            # Update address fields
            if 'first_name' in request.data:
                address.first_name = request.data['first_name']
            if 'last_name' in request.data:
                address.last_name = request.data['last_name']
            if 'company' in request.data:
                address.company = request.data['company']
            if 'address1' in request.data:
                address.address1 = request.data['address1']
            if 'address2' in request.data:
                address.address2 = request.data['address2']
            if 'city' in request.data:
                address.city = request.data['city']
            if 'province' in request.data:
                address.province = request.data['province']
            if 'country' in request.data:
                address.country = request.data['country']
            if 'zip_code' in request.data:
                address.zip_code = request.data['zip_code']
            if 'phone' in request.data:
                address.phone = request.data['phone']
            if 'is_default' in request.data:
                address.is_default = request.data['is_default']
            
            address.save()
            
            return Response({
                'success': True,
                'message': 'Address updated successfully'
            })
            
        except ShopifyCustomerAddress.DoesNotExist:
            return Response(
                {'error': 'Address not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def delete_address(self, request, pk=None):
        """Delete customer address"""
        try:
            address = ShopifyCustomerAddress.objects.get(pk=pk)
            address.delete()
            
            return Response({
                'success': True,
                'message': 'Address deleted successfully'
            })
            
        except ShopifyCustomerAddress.DoesNotExist:
            return Response(
                {'error': 'Address not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
