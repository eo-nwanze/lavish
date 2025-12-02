from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count
from .shopify_shipping_service import ShopifyCarrierServiceWebhook
from .shopify_sync_service import ShopifyShippingSyncService
from .models import ShopifyCarrierService, ShopifyDeliveryProfile, ShopifyDeliveryZone, ShopifyDeliveryMethod
import json
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carrier_service_list(request):
    """List all carrier services"""
    services = ShopifyCarrierService.objects.filter(active=True)
    return Response({
        'carrier_services': [{
            'id': service.id,
            'shopify_id': service.shopify_id,
            'name': service.name,
            'callback_url': service.callback_url,
            'service_discovery': service.service_discovery,
            'carrier_service_type': service.carrier_service_type,
            'format': service.format,
            'active': service.active
        } for service in services]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_profiles_list(request):
    """List all delivery profiles with zones and methods"""
    profiles = ShopifyDeliveryProfile.objects.filter(active=True).prefetch_related('zones__methods')
    
    return Response({
        'delivery_profiles': [{
            'id': profile.id,
            'shopify_id': profile.shopify_id,
            'name': profile.name,
            'default': profile.default,
            'zones': [{
                'id': zone.id,
                'shopify_id': zone.shopify_id,
                'name': zone.name,
                'countries': zone.countries,
                'methods': [{
                    'id': method.id,
                    'shopify_id': method.shopify_id,
                    'name': method.name,
                    'method_type': method.method_type
                } for method in zone.methods.all()]
            } for zone in profile.zones.all()]
        } for profile in profiles]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_shipping_data(request):
    """
    Trigger a sync of shipping data from Shopify
    
    POST /api/shipping/sync/
    {
      "sync_type": "all|carrier_services|delivery_profiles"
    }
    """
    sync_type = request.data.get('sync_type', 'all')
    
    service = ShopifyShippingSyncService()
    
    try:
        if sync_type == 'carrier_services':
            results = service.sync_carrier_services()
        elif sync_type == 'delivery_profiles':
            results = service.sync_delivery_profiles()
        else:  # 'all'
            results = service.sync_all_shipping_data()
        
        return Response({
            'success': True,
            'sync_type': sync_type,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Shipping sync failed: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipping_rates_query(request):
    """
    Query available shipping rates for an address
    
    GET /api/shipping/rates/?country=US&postal_code=10001
    """
    country = request.GET.get('country', 'US')
    postal_code = request.GET.get('postal_code', '')
    
    try:
        # Find applicable zones
        zones = ShopifyDeliveryZone.objects.filter(
            countries__icontains=country
        ).prefetch_related('methods', 'profile')
        
        rates = []
        
        for zone in zones:
            for method in zone.methods.all():
                rates.append({
                    'service_name': method.name,
                    'service_code': method.shopify_id,
                    'zone': zone.name,
                    'profile': zone.profile.name,
                    'method_type': method.method_type
                })
        
        return Response({
            'success': True,
            'country': country,
            'postal_code': postal_code,
            'available_rates': rates,
            'count': len(rates)
        })
        
    except Exception as e:
        logger.error(f"Failed to query shipping rates: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fulfillment_order_list(request):
    """
    List fulfillment orders with filtering and pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - order_id: Filter by order Shopify ID
    - status: Filter by fulfillment status
    - location_id: Filter by location ID
    """
    try:
        from .models import ShopifyFulfillmentOrder
        from orders.models import ShopifyOrder
        from django.core.paginator import Paginator
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        order_id = request.GET.get('order_id', '')
        status_filter = request.GET.get('status', '')
        location_id = request.GET.get('location_id', '')
        
        # Build base queryset
        queryset = ShopifyFulfillmentOrder.objects.select_related('order', 'location')
        
        # Apply filters
        if order_id:
            queryset = queryset.filter(order__shopify_id=order_id)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if location_id:
            queryset = queryset.filter(location__shopify_id=location_id)
        
        # Order by most recent
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize fulfillment orders
        fulfillment_orders_data = []
        for fulfillment_order in page_obj:
            fulfillment_orders_data.append({
                'id': fulfillment_order.id,
                'shopify_id': fulfillment_order.shopify_id,
                'order': {
                    'id': fulfillment_order.order.id,
                    'shopify_id': fulfillment_order.order.shopify_id,
                    'name': fulfillment_order.order.name,
                    'customer_email': fulfillment_order.order.customer_email,
                },
                'location': {
                    'id': fulfillment_order.location.id if fulfillment_order.location else None,
                    'shopify_id': fulfillment_order.location.shopify_id if fulfillment_order.location else None,
                    'name': fulfillment_order.location.name if fulfillment_order.location else None,
                } if fulfillment_order.location else None,
                'status': fulfillment_order.status,
                'request_status': fulfillment_order.request_status,
                'fulfill_at': fulfillment_order.fulfill_at.isoformat() if fulfillment_order.fulfill_at else None,
                'fulfill_by': fulfillment_order.fulfill_by.isoformat() if fulfillment_order.fulfill_by else None,
                'international_duties': fulfillment_order.international_duties,
                'delivery_method': fulfillment_order.delivery_method,
                'created_at': fulfillment_order.created_at.isoformat() if fulfillment_order.created_at else None,
                'updated_at': fulfillment_order.updated_at.isoformat() if fulfillment_order.updated_at else None,
                'line_items_count': fulfillment_order.line_items.count() if hasattr(fulfillment_order, 'line_items') else 0,
            })
        
        return Response({
            'success': True,
            'fulfillment_orders': fulfillment_orders_data,
            'pagination': {
                'total_orders': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'filters_applied': {
                'order_id': order_id,
                'status': status_filter,
                'location_id': location_id,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in fulfillment_order_list: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve fulfillment orders',
            'details': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fulfillment_order_detail(request, shopify_id):
    """
    Get detailed fulfillment order information
    
    Path Parameters:
    - shopify_id: Shopify fulfillment order ID
    """
    try:
        from .models import ShopifyFulfillmentOrder
        
        fulfillment_order = get_object_or_404(
            ShopifyFulfillmentOrder.objects.select_related('order', 'location'),
            shopify_id=shopify_id
        )
        
        fulfillment_order_data = {
            'id': fulfillment_order.id,
            'shopify_id': fulfillment_order.shopify_id,
            'order': {
                'id': fulfillment_order.order.id,
                'shopify_id': fulfillment_order.order.shopify_id,
                'name': fulfillment_order.order.name,
                'customer_email': fulfillment_order.order.customer_email,
                'total_price': str(fulfillment_order.order.total_price),
                'currency_code': fulfillment_order.order.currency_code,
                'financial_status': fulfillment_order.order.financial_status,
                'fulfillment_status': fulfillment_order.order.fulfillment_status,
            },
            'location': {
                'id': fulfillment_order.location.id if fulfillment_order.location else None,
                'shopify_id': fulfillment_order.location.shopify_id if fulfillment_order.location else None,
                'name': fulfillment_order.location.name if fulfillment_order.location else None,
                'address1': fulfillment_order.location.address1 if fulfillment_order.location else None,
                'city': fulfillment_order.location.city if fulfillment_order.location else None,
                'province': fulfillment_order.location.province if fulfillment_order.location else None,
                'country': fulfillment_order.location.country if fulfillment_order.location else None,
                'zip': fulfillment_order.location.zip if fulfillment_order.location else None,
            } if fulfillment_order.location else None,
            'status': fulfillment_order.status,
            'request_status': fulfillment_order.request_status,
            'fulfill_at': fulfillment_order.fulfill_at.isoformat() if fulfillment_order.fulfill_at else None,
            'fulfill_by': fulfillment_order.fulfill_by.isoformat() if fulfillment_order.fulfill_by else None,
            'international_duties': fulfillment_order.international_duties,
            'delivery_method': fulfillment_order.delivery_method,
            'created_at': fulfillment_order.created_at.isoformat() if fulfillment_order.created_at else None,
            'updated_at': fulfillment_order.updated_at.isoformat() if fulfillment_order.updated_at else None,
            'store_domain': fulfillment_order.store_domain,
        }
        
        return Response({
            'success': True,
            'fulfillment_order': fulfillment_order_data
        })
        
    except Exception as e:
        logger.error(f"Error in fulfillment_order_detail: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve fulfillment order details',
            'details': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fulfillment_create(request):
    """
    Create a new fulfillment for an order
    
    POST Data:
    {
        "order_shopify_id": "gid://shopify/Order/123456789",
        "location_shopify_id": "gid://shopify/Location/987654321",
        "tracking_numbers": ["1Z999AA10123456784"],
        "tracking_urls": ["https://www.ups.com/tracking/1Z999AA10123456784"],
        "tracking_company": "UPS",
        "notify_customer": true,
        "line_items": [
            {
                "shopify_id": "gid://shopify/LineItem/123456789",
                "quantity": 1
            }
        ]
    }
    """
    try:
        from .models import ShopifyFulfillmentOrder
        from orders.models import ShopifyOrder
        from shopify_integration.client import ShopifyAPIClient
        from django.shortcuts import get_object_or_404
        
        # Get request data
        order_shopify_id = request.data.get('order_shopify_id')
        location_shopify_id = request.data.get('location_shopify_id')
        tracking_numbers = request.data.get('tracking_numbers', [])
        tracking_urls = request.data.get('tracking_urls', [])
        tracking_company = request.data.get('tracking_company', '')
        notify_customer = request.data.get('notify_customer', True)
        line_items = request.data.get('line_items', [])
        
        if not order_shopify_id or not location_shopify_id:
            return Response({
                'success': False,
                'error': 'order_shopify_id and location_shopify_id are required'
            }, status=400)
        
        # Get order
        order = get_object_or_404(ShopifyOrder, shopify_id=order_shopify_id)
        
        # Create fulfillment via Shopify API
        client = ShopifyAPIClient()
        
        # Prepare line items for fulfillment
        fulfillment_line_items = []
        for item in line_items:
            fulfillment_line_items.append({
                'id': item['shopify_id'],
                'quantity': item['quantity']
            })
        
        # Create fulfillment in Shopify
        fulfillment_data = {
            'fulfillment': {
                'location_id': location_shopify_id,
                'tracking_company': tracking_company,
                'tracking_numbers': tracking_numbers,
                'tracking_urls': tracking_urls,
                'notify_customer': notify_customer,
                'line_items': fulfillment_line_items
            }
        }
        
        # Call Shopify API to create fulfillment
        result = client.create_fulfillment(order_shopify_id, fulfillment_data)
        
        if result and 'fulfillment' in result:
            fulfillment = result['fulfillment']
            
            # Update order fulfillment status
            if fulfillment.get('status') == 'success':
                order.fulfillment_status = 'fulfilled'
                order.save()
            
            return Response({
                'success': True,
                'message': 'Fulfillment created successfully',
                'fulfillment': {
                    'shopify_id': fulfillment.get('id'),
                    'status': fulfillment.get('status'),
                    'tracking_company': fulfillment.get('tracking_company'),
                    'tracking_numbers': fulfillment.get('tracking_numbers'),
                    'tracking_urls': fulfillment.get('tracking_urls'),
                    'created_at': fulfillment.get('created_at'),
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to create fulfillment in Shopify',
                'details': result
            }, status=500)
    
    except Exception as e:
        logger.error(f"Error in fulfillment_create: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to create fulfillment',
            'details': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fulfillment_update_tracking(request, shopify_id):
    """
    Update tracking information for a fulfillment
    
    POST Data:
    {
        "tracking_numbers": ["1Z999AA10123456784"],
        "tracking_urls": ["https://www.ups.com/tracking/1Z999AA10123456784"],
        "tracking_company": "UPS",
        "notify_customer": true
    }
    """
    try:
        from .models import ShopifyFulfillmentOrder
        from shopify_integration.client import ShopifyAPIClient
        
        # Get fulfillment order
        fulfillment_order = get_object_or_404(ShopifyFulfillmentOrder, shopify_id=shopify_id)
        
        # Get request data
        tracking_numbers = request.data.get('tracking_numbers', [])
        tracking_urls = request.data.get('tracking_urls', [])
        tracking_company = request.data.get('tracking_company', '')
        notify_customer = request.data.get('notify_customer', True)
        
        if not tracking_numbers:
            return Response({
                'success': False,
                'error': 'At least one tracking number is required'
            }, status=400)
        
        # Update fulfillment via Shopify API
        client = ShopifyAPIClient()
        
        update_data = {
            'fulfillment': {
                'tracking_company': tracking_company,
                'tracking_numbers': tracking_numbers,
                'tracking_urls': tracking_urls,
                'notify_customer': notify_customer
            }
        }
        
        # Call Shopify API to update fulfillment
        result = client.update_fulfillment_tracking(shopify_id, update_data)
        
        if result and 'fulfillment' in result:
            fulfillment = result['fulfillment']
            
            return Response({
                'success': True,
                'message': 'Tracking information updated successfully',
                'fulfillment': {
                    'shopify_id': fulfillment.get('id'),
                    'tracking_company': fulfillment.get('tracking_company'),
                    'tracking_numbers': fulfillment.get('tracking_numbers'),
                    'tracking_urls': fulfillment.get('tracking_urls'),
                    'updated_at': fulfillment.get('updated_at'),
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to update tracking information',
                'details': result
            }, status=500)
    
    except Exception as e:
        logger.error(f"Error in fulfillment_update_tracking: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to update tracking information',
            'details': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fulfillment_cancel(request, shopify_id):
    """
    Cancel a fulfillment
    
    POST Data:
    {
        "reason": "Customer requested cancellation"
    }
    """
    try:
        from .models import ShopifyFulfillmentOrder
        from shopify_integration.client import ShopifyAPIClient
        
        # Get fulfillment order
        fulfillment_order = get_object_or_404(ShopifyFulfillmentOrder, shopify_id=shopify_id)
        
        # Check if fulfillment can be cancelled
        if fulfillment_order.status in ['closed', 'cancelled']:
            return Response({
                'success': False,
                'error': f'Cannot cancel fulfillment with status: {fulfillment_order.status}'
            }, status=400)
        
        # Get cancellation reason
        reason = request.data.get('reason', 'Requested by merchant')
        
        # Cancel fulfillment via Shopify API
        client = ShopifyAPIClient()
        
        result = client.cancel_fulfillment(shopify_id, reason)
        
        if result and 'fulfillment' in result:
            fulfillment = result['fulfillment']
            
            # Update local fulfillment order status
            fulfillment_order.status = 'cancelled'
            fulfillment_order.request_status = 'cancellation_accepted'
            fulfillment_order.save()
            
            # Update order fulfillment status
            order = fulfillment_order.order
            order.fulfillment_status = 'null'  # Reset to unfulfilled
            order.save()
            
            return Response({
                'success': True,
                'message': 'Fulfillment cancelled successfully',
                'fulfillment': {
                    'shopify_id': fulfillment.get('id'),
                    'status': fulfillment.get('status'),
                    'cancelled_at': fulfillment.get('cancelled_at'),
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to cancel fulfillment',
                'details': result
            }, status=500)
    
    except Exception as e:
        logger.error(f"Error in fulfillment_cancel: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to cancel fulfillment',
            'details': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fulfillment_statistics(request):
    """
    Get fulfillment statistics and analytics
    
    Query Parameters:
    - days: Number of days to analyze (default: 30)
    - status: Filter by status
    """
    try:
        from .models import ShopifyFulfillmentOrder
        from datetime import datetime, timedelta
        
        days = int(request.GET.get('days', 30))
        status_filter = request.GET.get('status', '')
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset for the date range
        queryset = ShopifyFulfillmentOrder.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Apply status filter if provided
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Calculate statistics
        stats = queryset.aggregate(
            total_fulfillments=Count('id'),
            open_fulfillments=Count('id', filter=Q(status='open')),
            in_progress_fulfillments=Count('id', filter=Q(status='in_progress')),
            closed_fulfillments=Count('id', filter=Q(status='closed')),
            cancelled_fulfillments=Count('id', filter=Q(status='cancelled')),
        )
        
        # Status breakdown
        status_breakdown = {}
        for status_choice in ShopifyFulfillmentOrder.STATUS_CHOICES:
            status = status_choice[0]
            count = queryset.filter(status=status).count()
            if count > 0:
                status_breakdown[status] = count
        
        # Request status breakdown
        request_status_breakdown = {}
        for status_choice in ShopifyFulfillmentOrder.REQUEST_STATUS_CHOICES:
            status = status_choice[0]
            count = queryset.filter(request_status=status).count()
            if count > 0:
                request_status_breakdown[status] = count
        
        return Response({
            'success': True,
            'period': {
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'days': days
            },
            'summary': {
                'total_fulfillments': stats['total_fulfillments'],
                'open_fulfillments': stats['open_fulfillments'],
                'in_progress_fulfillments': stats['in_progress_fulfillments'],
                'closed_fulfillments': stats['closed_fulfillments'],
                'cancelled_fulfillments': stats['cancelled_fulfillments'],
            },
            'status_breakdown': {
                'fulfillment_status': status_breakdown,
                'request_status': request_status_breakdown
            }
        })
        
    except Exception as e:
        logger.error(f"Error in fulfillment_statistics: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve fulfillment statistics',
            'details': str(e)
        }, status=500)


@csrf_exempt
def calculate_shipping_rates(request):
    """
    Shopify Carrier Service Callback Endpoint
    
    This endpoint is called by Shopify during checkout to get live shipping rates.
    
    Request format:
    {
      "rate": {
        "origin": {
          "country": "CA",
          "postal_code": "K2P1L4",
          "province": "ON",
          "city": "Ottawa",
          "name": null,
          "address1": "150 Elgin St.",
          "address2": "",
          "address3": null
        },
        "destination": {
          "country": "CA",
          "postal_code": "K1M1M4",
          "province": "ON",
          "city": "Ottawa",
          "name": "John Doe",
          "address1": "123 Main St",
          "address2": "",
          "address3": null
        },
        "items": [{
          "name": "Product Name",
          "sku": "ABC123",
          "quantity": 1,
          "grams": 1000,
          "price": 2999,
          "vendor": "Vendor Name",
          "requires_shipping": true,
          "taxable": true,
          "fulfillment_service": "manual",
          "properties": null,
          "product_id": 123456,
          "variant_id": 789012
        }],
        "currency": "CAD",
        "locale": "en-CA"
      }
    }
    
    Response format (Shopify ShippingRate object):
    {
      "rates": [{
        "handle": "standard-shipping",
        "title": "Standard Shipping",
        "price": {
          "amount": "5.99",
          "currencyCode": "CAD"
        },
        "description": "5-7 business days",
        "min_delivery_date": "2024-01-20",
        "max_delivery_date": "2024-01-25"
      }]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'rates': []}, status=400)
    
    try:
        # Log the incoming request for debugging
        logger.info(f"Received shipping rate request from Shopify")
        
        # Parse JSON body
        data = json.loads(request.body)
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        
        # Handle the rate request
        response = ShopifyCarrierServiceWebhook.handle_rate_request(data)
        
        # Log the response
        logger.info(f"Returning {len(response.get('rates', []))} shipping rates")
        logger.debug(f"Response: {json.dumps(response, indent=2)}")
        
        return JsonResponse(response)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        return JsonResponse({'rates': []}, status=400)
    except Exception as e:
        logger.error(f"Error calculating shipping rates: {str(e)}", exc_info=True)
        return JsonResponse({'rates': []}, status=500)


@api_view(['POST'])
def test_shipping_rates(request):
    """
    Test endpoint to simulate Shopify rate request
    Useful for testing without going through actual Shopify checkout
    
    Usage:
    POST /api/shipping/test-rates/
    {
      "origin_country": "US",
      "origin_postal_code": "10001",
      "destination_country": "US",
      "destination_postal_code": "90210",
      "weight_grams": 1000,
      "value_cents": 2999,
      "currency": "USD"
    }
    """
    try:
        # Build a Shopify-style rate request from simple input
        origin_country = request.data.get('origin_country', 'US')
        origin_postal = request.data.get('origin_postal_code', '10001')
        dest_country = request.data.get('destination_country', 'US')
        dest_postal = request.data.get('destination_postal_code', '90210')
        weight = request.data.get('weight_grams', 1000)
        value = request.data.get('value_cents', 2999)
        currency = request.data.get('currency', 'USD')
        
        rate_request = {
            'rate': {
                'origin': {
                    'country': origin_country,
                    'postal_code': origin_postal,
                    'province': '',
                    'city': '',
                    'name': None,
                    'address1': '',
                    'address2': '',
                    'address3': None
                },
                'destination': {
                    'country': dest_country,
                    'postal_code': dest_postal,
                    'province': '',
                    'city': '',
                    'name': 'Test Customer',
                    'address1': 'Test Address',
                    'address2': '',
                    'address3': None
                },
                'items': [{
                    'name': 'Test Product',
                    'sku': 'TEST-SKU',
                    'quantity': 1,
                    'grams': weight,
                    'price': value,
                    'vendor': 'Test Vendor',
                    'requires_shipping': True,
                    'taxable': True,
                    'fulfillment_service': 'manual',
                    'properties': None,
                    'product_id': 123456,
                    'variant_id': 789012
                }],
                'currency': currency,
                'locale': 'en-US'
            }
        }
        
        # Calculate rates
        response = ShopifyCarrierServiceWebhook.handle_rate_request(rate_request)
        
        return Response({
            'success': True,
            'request': rate_request,
            'response': response
        })
        
    except Exception as e:
        logger.error(f"Test shipping rates error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
