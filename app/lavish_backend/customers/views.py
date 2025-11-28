from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ShopifyCustomer
from .services import CustomerSyncService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_list(request):
    """List all customers"""
    customers = ShopifyCustomer.objects.all()[:50]  # Limit to 50 for performance
    data = []
    
    for customer in customers:
        data.append({
            'shopify_id': customer.shopify_id,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
            'state': customer.state,
            'verified_email': customer.verified_email,
            'number_of_orders': customer.number_of_orders,
            'tags': customer.get_tags_list(),
            'created_at': customer.created_at,
            'updated_at': customer.updated_at,
        })
    
    return Response({'customers': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_detail(request, shopify_id):
    """Get customer details"""
    try:
        customer = ShopifyCustomer.objects.get(shopify_id=shopify_id)
        
        # Get addresses
        addresses = []
        for address in customer.addresses.all():
            addresses.append({
                'shopify_id': address.shopify_id,
                'first_name': address.first_name,
                'last_name': address.last_name,
                'company': address.company,
                'address1': address.address1,
                'address2': address.address2,
                'city': address.city,
                'province': address.province,
                'country': address.country,
                'zip_code': address.zip_code,
                'phone': address.phone,
                'is_default': address.is_default,
            })
        
        data = {
            'shopify_id': customer.shopify_id,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
            'state': customer.state,
            'verified_email': customer.verified_email,
            'tax_exempt': customer.tax_exempt,
            'number_of_orders': customer.number_of_orders,
            'total_spent': str(customer.total_spent),
            'tags': customer.get_tags_list(),
            'addresses': addresses,
            'created_at': customer.created_at,
            'updated_at': customer.updated_at,
            'last_synced': customer.last_synced,
            'sync_status': customer.sync_status,
        }
        
        return Response(data)
        
    except ShopifyCustomer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_customers(request):
    """Trigger customer synchronization"""
    try:
        service = CustomerSyncService()
        sync_log = service.sync_all_customers()
        
        return Response({
            'status': 'success',
            'message': 'Customer synchronization completed',
            'customers_processed': sync_log.customers_processed,
            'customers_created': sync_log.customers_created,
            'customers_updated': sync_log.customers_updated,
            'errors_count': sync_log.errors_count,
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
