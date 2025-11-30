from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .shopify_shipping_service import ShopifyCarrierServiceWebhook
from .models import ShopifyCarrierService
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
            'service_discovery': service.service_discovery
        } for service in services]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fulfillment_order_list(request):
    """List fulfillment orders"""
    return Response({'fulfillment_orders': []})


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
    
    Response format:
    {
      "rates": [{
        "service_name": "Standard Shipping",
        "service_code": "standard",
        "total_price": "599",
        "currency": "CAD",
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
