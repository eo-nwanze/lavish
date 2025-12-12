"""
Frontend API Views
Direct API endpoints for frontend JavaScript calls
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from customers.models import ShopifyCustomer, ShopifyCustomerAddress
from orders.models import ShopifyOrder, ShopifyOrderAddress


@api_view(['POST'])
@permission_classes([AllowAny])
def update_customer_profile(request):
    """Update customer profile information"""
    try:
        # Use request.data for DRF Request objects
        data = request.data
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return Response(
                {'success': False, 'error': 'Customer ID required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customer = ShopifyCustomer.objects.get(shopify_id=customer_id)
        
        # Update customer fields
        if 'first_name' in data:
            customer.first_name = data['first_name']
        if 'last_name' in data:
            customer.last_name = data['last_name']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'email' in data:
            customer.email = data['email']
        if 'accepts_marketing' in data:
            customer.accepts_marketing = data['accepts_marketing']
        
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
            {'success': False, 'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_customer_address(request):
    """Create new customer address"""
    try:
        # Use request.data for DRF Request objects
        data = request.data
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return Response(
                {'success': False, 'error': 'Customer ID required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customer = ShopifyCustomer.objects.get(shopify_id=customer_id)
        
        # Create address
        address = ShopifyCustomerAddress.objects.create(
            customer=customer,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            company=data.get('company', ''),
            address1=data.get('address1', ''),
            address2=data.get('address2', ''),
            city=data.get('city', ''),
            province=data.get('province', ''),
            country=data.get('country', ''),
            zip_code=data.get('zip_code', ''),
            phone=data.get('phone', ''),
            is_default=data.get('is_default', False)
        )
        
        return Response({
            'success': True,
            'message': 'Address created successfully',
            'address_id': address.id,
            'shopify_id': address.shopify_id
        }, status=status.HTTP_201_CREATED)
        
    except ShopifyCustomer.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def update_customer_address(request, address_id):
    """Update customer address"""
    try:
        # Use request.data for DRF Request objects
        data = request.data
        address = ShopifyCustomerAddress.objects.get(pk=address_id)
        
        # Update address fields
        if 'first_name' in data:
            address.first_name = data['first_name']
        if 'last_name' in data:
            address.last_name = data['last_name']
        if 'company' in data:
            address.company = data['company']
        if 'address1' in data:
            address.address1 = data['address1']
        if 'address2' in data:
            address.address2 = data['address2']
        if 'city' in data:
            address.city = data['city']
        if 'province' in data:
            address.province = data['province']
        if 'country' in data:
            address.country = data['country']
        if 'zip_code' in data:
            address.zip_code = data['zip_code']
        if 'phone' in data:
            address.phone = data['phone']
        if 'is_default' in data:
            address.is_default = data['is_default']
        
        address.save()
        
        return Response({
            'success': True,
            'message': 'Address updated successfully'
        })
        
    except ShopifyCustomerAddress.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Address not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_customer_address(request, address_id):
    """Delete customer address"""
    try:
        address = ShopifyCustomerAddress.objects.get(pk=address_id)
        address.delete()
        
        return Response({
            'success': True,
            'message': 'Address deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
        
    except ShopifyCustomerAddress.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Address not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def update_order_address(request, order_id):
    """Update order shipping address"""
    try:
        # Use request.data for DRF Request objects
        data = request.data
        order = ShopifyOrder.objects.get(shopify_id=order_id)
        
        # Get or create shipping address
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
        address_data = data.get('address', {})
        
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
        
    except ShopifyOrder.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_order(request, order_id):
    """Cancel an order"""
    try:
        order = ShopifyOrder.objects.get(shopify_id=order_id)
        
        # Check if order can be cancelled
        # Orders that are already refunded or voided cannot be cancelled
        if order.financial_status in ['refunded', 'voided', 'partially_refunded']:
            return Response(
                {'success': False, 'error': 'Order cannot be cancelled - already refunded or voided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check fulfillment status - cannot cancel fulfilled orders
        if order.fulfillment_status == 'fulfilled':
            return Response(
                {'success': False, 'error': 'Order cannot be cancelled - already fulfilled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update order status to 'voided' (correct financial_status for cancelled orders)
        order.financial_status = 'voided'
        
        # Store cancellation reason in notes field (cancelled_at and cancel_reason don't exist in model)
        cancellation_reason = request.data.get('reason', 'Customer requested cancellation')
        cancellation_note = f"[CANCELLED {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] {cancellation_reason}"
        
        # Append to existing notes if any
        if order.note:
            order.note = f"{order.note}\n\n{cancellation_note}"
        else:
            order.note = cancellation_note
        
        order.save()
        
        return Response({
            'success': True,
            'message': 'Order cancelled successfully',
            'order': {
                'shopify_id': order.shopify_id,
                'name': order.name,
                'financial_status': order.financial_status,
                'updated_at': order.updated_at.isoformat()
            }
        })
        
    except ShopifyOrder.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def download_order_invoice(request, order_id):
    """Generate and download order invoice"""
    try:
        order = ShopifyOrder.objects.get(shopify_id=order_id)
        
        # Generate invoice PDF (simplified version)
        # In a real implementation, you would use a PDF library like ReportLab
        invoice_data = {
            'order_name': order.name,
            'customer_email': order.customer_email,
            'created_at': order.created_at.isoformat(),
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
        
    except ShopifyOrder.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
