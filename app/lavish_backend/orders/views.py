from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
import logging

from .models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress
from shopify_integration.client import ShopifyAPIClient
from .realtime_sync import RealtimeOrderSyncService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """
    List all orders with filtering, pagination, and search
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - search: Search by order name, email, or customer name
    - financial_status: Filter by financial status (pending, paid, partially_paid, refunded, partially_refunded, voided)
    - fulfillment_status: Filter by fulfillment status (fulfilled, null, partial, restocked)
    - date_from: Filter orders created after this date (ISO format)
    - date_to: Filter orders created before this date (ISO format)
    - sort_by: Sort field (created_at, updated_at, total_price, name)
    - sort_order: Sort direction (asc, desc)
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 items
        search = request.GET.get('search', '').strip()
        financial_status = request.GET.get('financial_status', '')
        fulfillment_status = request.GET.get('fulfillment_status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')
        
        # Build base queryset
        queryset = ShopifyOrder.objects.select_related().prefetch_related(
            'line_items', 'addresses', 'fulfillment_orders'
        )
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(customer_email__icontains=search) |
                Q(customer_phone__icontains=search)
            )
        
        if financial_status:
            queryset = queryset.filter(financial_status=financial_status)
        
        if fulfillment_status:
            queryset = queryset.filter(fulfillment_status=fulfillment_status)
        
        if date_from:
            try:
                date_from_dt = parse_datetime(date_from)
                if date_from_dt:
                    queryset = queryset.filter(created_at__gte=date_from_dt)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_dt = parse_datetime(date_to)
                if date_to_dt:
                    queryset = queryset.filter(created_at__lte=date_to_dt)
            except ValueError:
                pass
        
        # Apply sorting
        valid_sort_fields = ['created_at', 'updated_at', 'total_price', 'name', 'financial_status', 'fulfillment_status']
        if sort_by in valid_sort_fields:
            sort_direction = '-' if sort_order == 'desc' else ''
            queryset = queryset.order_by(f'{sort_direction}{sort_by}')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize orders
        orders_data = []
        for order in page_obj:
            orders_data.append({
                'id': order.id,
                'shopify_id': order.shopify_id,
                'name': order.name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'total_price': str(order.total_price),
                'currency_code': order.currency_code,
                'financial_status': order.financial_status,
                'fulfillment_status': order.fulfillment_status,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'processed_at': order.processed_at.isoformat() if order.processed_at else None,
                'line_items_count': order.line_items.count(),
                'addresses_count': order.addresses.count(),
                'fulfillment_orders_count': order.fulfillment_orders.count(),
                'tags': order.tags,
                'note': order.note,
                'last_synced': order.last_synced.isoformat() if order.last_synced else None,
            })
        
        # Calculate statistics
        stats = {
            'total_orders': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        
        # Add summary statistics
        summary_stats = queryset.aggregate(
            total_revenue=Sum('total_price'),
            avg_order_value=Avg('total_price'),
            orders_count=Count('id')
        )
        
        return Response({
            'success': True,
            'orders': orders_data,
            'pagination': stats,
            'summary': {
                'total_revenue': str(summary_stats['total_revenue'] or 0),
                'avg_order_value': str(summary_stats['avg_order_value'] or 0),
                'orders_count': summary_stats['orders_count']
            },
            'filters_applied': {
                'search': search,
                'financial_status': financial_status,
                'fulfillment_status': fulfillment_status,
                'date_from': date_from,
                'date_to': date_to,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        })
        
    except Exception as e:
        logger.error(f"Error in order_list: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve orders',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, shopify_id):
    """
    Get detailed order information including line items and addresses
    
    Path Parameters:
    - shopify_id: Shopify order ID
    
    Query Parameters:
    - include_line_items: Include line items (default: true)
    - include_addresses: Include addresses (default: true)
    - include_fulfillments: Include fulfillment information (default: true)
    """
    try:
        # Get query parameters
        include_line_items = request.GET.get('include_line_items', 'true').lower() == 'true'
        include_addresses = request.GET.get('include_addresses', 'true').lower() == 'true'
        include_fulfillments = request.GET.get('include_fulfillments', 'true').lower() == 'true'
        
        # Get order with related data
        queryset = ShopifyOrder.objects.select_related()
        if include_line_items:
            queryset = queryset.prefetch_related('line_items')
        if include_addresses:
            queryset = queryset.prefetch_related('addresses')
        if include_fulfillments:
            queryset = queryset.prefetch_related('fulfillment_orders')
        
        order = get_object_or_404(queryset, shopify_id=shopify_id)
        
        # Base order data
        order_data = {
            'id': order.id,
            'shopify_id': order.shopify_id,
            'name': order.name,
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
            'customer_shopify_id': order.customer_shopify_id,
            'total_price': str(order.total_price),
            'currency_code': order.currency_code,
            'financial_status': order.financial_status,
            'fulfillment_status': order.fulfillment_status,
            'subtotal_price': str(order.subtotal_price),
            'total_tax': str(order.total_tax),
            'total_shipping_price': str(order.total_shipping_price),
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'processed_at': order.processed_at.isoformat() if order.processed_at else None,
            'cancelled_at': order.cancelled_at.isoformat() if order.cancelled_at else None,
            'tags': order.tags,
            'note': order.note,
            'last_synced': order.last_synced.isoformat() if order.last_synced else None,
            'store_domain': order.store_domain,
        }
        
        # Add line items
        if include_line_items:
            line_items_data = []
            for line_item in order.line_items.all():
                line_items_data.append({
                    'id': line_item.id,
                    'shopify_id': line_item.shopify_id,
                    'title': line_item.title,
                    'quantity': line_item.quantity,
                    'price': str(line_item.price),
                    'variant_shopify_id': line_item.variant_shopify_id,
                    'variant_title': line_item.variant_title,
                    'variant_sku': line_item.variant_sku,
                    'product_shopify_id': line_item.product_shopify_id,
                    'product_title': line_item.product_title,
                    'last_synced': line_item.last_synced.isoformat() if line_item.last_synced else None,
                })
            order_data['line_items'] = line_items_data
        
        # Add addresses
        if include_addresses:
            addresses_data = []
            for address in order.addresses.all():
                addresses_data.append({
                    'id': address.id,
                    'address_type': address.address_type,
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
                    'last_synced': address.last_synced.isoformat() if address.last_synced else None,
                })
            order_data['addresses'] = addresses_data
        
        # Add fulfillment information
        if include_fulfillments:
            fulfillments_data = []
            for fulfillment_order in order.fulfillment_orders.all():
                fulfillments_data.append({
                    'id': fulfillment_order.id,
                    'shopify_id': fulfillment_order.shopify_id,
                    'status': fulfillment_order.status,
                    'request_status': fulfillment_order.request_status,
                    'fulfill_at': fulfillment_order.fulfill_at.isoformat() if fulfillment_order.fulfill_at else None,
                    'fulfill_by': fulfillment_order.fulfill_by.isoformat() if fulfillment_order.fulfill_by else None,
                    'delivery_method': fulfillment_order.delivery_method,
                    'international_duties': fulfillment_order.international_duties,
                    'created_at': fulfillment_order.created_at.isoformat() if fulfillment_order.created_at else None,
                    'updated_at': fulfillment_order.updated_at.isoformat() if fulfillment_order.updated_at else None,
                })
            order_data['fulfillment_orders'] = fulfillments_data
        
        return Response({
            'success': True,
            'order': order_data
        })
        
    except Exception as e:
        logger.error(f"Error in order_detail: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve order details',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_sync(request):
    """
    Trigger order synchronization from Shopify
    
    POST Data:
    {
        "sync_type": "all|recent|single",
        "limit": 50,  // Optional, for sync_type "all" or "recent"
        "shopify_id": "gid://shopify/Order/123456789"  // Required for sync_type "single"
    }
    """
    try:
        sync_type = request.data.get('sync_type', 'recent')
        limit = request.data.get('limit', 50)
        shopify_id = request.data.get('shopify_id')
        
        sync_service = RealtimeOrderSyncService()
        
        if sync_type == 'single':
            if not shopify_id:
                return Response({
                    'success': False,
                    'error': 'shopify_id is required for single order sync'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Sync single order
            client = ShopifyAPIClient()
            order_data = client.get_order(shopify_id)
            
            if not order_data:
                return Response({
                    'success': False,
                    'error': f'Order {shopify_id} not found in Shopify'
                }, status=status.HTTP_404_NOT_FOUND)
            
            result = sync_service._sync_single_order(order_data)
            
            return Response({
                'success': True,
                'message': f'Successfully synced order {result["order"].name}',
                'order': {
                    'id': result['order'].id,
                    'name': result['order'].name,
                    'created': result['created'],
                    'line_items_synced': result['line_items_synced']
                }
            })
        
        else:  # sync_type "all" or "recent"
            result = sync_service.sync_all_orders(limit=limit)
            
            return Response({
                'success': result['success'],
                'message': result['message'],
                'stats': result['stats']
            })
    
    except Exception as e:
        logger.error(f"Error in order_sync: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Order synchronization failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_statistics(request):
    """
    Get order statistics and analytics
    
    Query Parameters:
    - days: Number of days to analyze (default: 30)
    - status: Filter by status (financial or fulfillment)
    """
    try:
        days = int(request.GET.get('days', 30))
        status_filter = request.GET.get('status', '')
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset for the date range
        queryset = ShopifyOrder.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Apply status filter if provided
        if status_filter:
            queryset = queryset.filter(
                Q(financial_status=status_filter) | 
                Q(fulfillment_status=status_filter)
            )
        
        # Calculate statistics
        stats = queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price'),
            avg_order_value=Avg('total_price'),
            pending_orders=Count('id', filter=Q(financial_status='pending')),
            paid_orders=Count('id', filter=Q(financial_status='paid')),
            fulfilled_orders=Count('id', filter=Q(fulfillment_status='fulfilled')),
            unfulfilled_orders=Count('id', filter=Q(fulfillment_status='null')),
        )
        
        # Daily breakdown
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            day_stats = queryset.filter(
                created_at__date=current_date.date()
            ).aggregate(
                orders=Count('id'),
                revenue=Sum('total_price')
            )
            
            daily_stats.append({
                'date': current_date.date().isoformat(),
                'orders': day_stats['orders'] or 0,
                'revenue': str(day_stats['revenue'] or 0),
            })
            current_date += timedelta(days=1)
        
        # Status breakdown
        financial_status_breakdown = {}
        fulfillment_status_breakdown = {}
        
        for status_choice in ShopifyOrder.FINANCIAL_STATUS_CHOICES:
            status = status_choice[0]
            count = queryset.filter(financial_status=status).count()
            if count > 0:
                financial_status_breakdown[status] = count
        
        for status_choice in ShopifyOrder.FULFILLMENT_STATUS_CHOICES:
            status = status_choice[0]
            count = queryset.filter(fulfillment_status=status).count()
            if count > 0:
                fulfillment_status_breakdown[status] = count
        
        return Response({
            'success': True,
            'period': {
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'days': days
            },
            'summary': {
                'total_orders': stats['total_orders'],
                'total_revenue': str(stats['total_revenue'] or 0),
                'avg_order_value': str(stats['avg_order_value'] or 0),
                'pending_orders': stats['pending_orders'],
                'paid_orders': stats['paid_orders'],
                'fulfilled_orders': stats['fulfilled_orders'],
                'unfulfilled_orders': stats['unfulfilled_orders'],
            },
            'status_breakdown': {
                'financial': financial_status_breakdown,
                'fulfillment': fulfillment_status_breakdown
            },
            'daily_breakdown': daily_stats
        })
        
    except Exception as e:
        logger.error(f"Error in order_statistics: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve order statistics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_update_status(request, shopify_id):
    """
    Update order status (financial or fulfillment)
    
    POST Data:
    {
        "financial_status": "paid|pending|refunded|etc",
        "fulfillment_status": "fulfilled|null|partial|etc",
        "note": "Optional note about the status change"
    }
    """
    try:
        order = get_object_or_404(ShopifyOrder, shopify_id=shopify_id)
        
        financial_status = request.data.get('financial_status')
        fulfillment_status = request.data.get('fulfillment_status')
        note = request.data.get('note', '')
        
        # Validate status values
        if financial_status:
            valid_statuses = [choice[0] for choice in ShopifyOrder.FINANCIAL_STATUS_CHOICES]
            if financial_status not in valid_statuses:
                return Response({
                    'success': False,
                    'error': f'Invalid financial_status. Must be one of: {valid_statuses}'
                }, status=status.HTTP_400_BAD_REQUEST)
            order.financial_status = financial_status
        
        if fulfillment_status:
            valid_statuses = [choice[0] for choice in ShopifyOrder.FULFILLMENT_STATUS_CHOICES]
            if fulfillment_status not in valid_statuses:
                return Response({
                    'success': False,
                    'error': f'Invalid fulfillment_status. Must be one of: {valid_statuses}'
                }, status=status.HTTP_400_BAD_REQUEST)
            order.fulfillment_status = fulfillment_status
        
        # Add note if provided
        if note:
            if order.note:
                order.note = f"{order.note}\n\nStatus Update: {note}"
            else:
                order.note = f"Status Update: {note}"
        
        order.save()
        
        return Response({
            'success': True,
            'message': f'Order {order.name} status updated successfully',
            'order': {
                'id': order.id,
                'shopify_id': order.shopify_id,
                'name': order.name,
                'financial_status': order.financial_status,
                'fulfillment_status': order.fulfillment_status,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in order_update_status: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to update order status',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_orders(request):
    """
    Get orders for the currently authenticated customer
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status: Filter by financial status
    - date_from: Filter orders created after this date
    - date_to: Filter orders created before this date
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Get customer email from authenticated user
        customer_email = request.user.email
        
        # Build base queryset for customer's orders
        queryset = ShopifyOrder.objects.filter(
            customer_email=customer_email
        ).select_related().prefetch_related('line_items')
        
        # Apply filters
        if status_filter:
            queryset = queryset.filter(financial_status=status_filter)
        
        if date_from:
            try:
                date_from_dt = parse_datetime(date_from)
                if date_from_dt:
                    queryset = queryset.filter(created_at__gte=date_from_dt)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_dt = parse_datetime(date_to)
                if date_to_dt:
                    queryset = queryset.filter(created_at__lte=date_to_dt)
            except ValueError:
                pass
        
        # Order by most recent
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize orders with enhanced data
        orders_data = []
        for order in page_obj:
            # Get line items with image URLs
            line_items_data = []
            for line_item in order.line_items.all():
                line_items_data.append({
                    'id': line_item.id,
                    'shopify_id': line_item.shopify_id,
                    'title': line_item.title,
                    'quantity': line_item.quantity,
                    'price': str(line_item.price),
                    'variant_title': line_item.variant_title,
                    'variant_sku': line_item.variant_sku,
                    'variant_shopify_id': line_item.variant_shopify_id,
                    'product_title': line_item.product_title,
                    'product_shopify_id': line_item.product_shopify_id,
                    'image': None,  # Would need to fetch from Shopify API
                })
            
            orders_data.append({
                'id': order.id,
                'shopify_id': order.shopify_id,
                'name': order.name,
                'customer_email': order.customer_email,
                'total_price': str(order.total_price),
                'currency_code': order.currency_code,
                'financial_status': order.financial_status,
                'fulfillment_status': order.fulfillment_status,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'processed_at': order.processed_at.isoformat() if order.processed_at else None,
                'cancelled_at': order.cancelled_at.isoformat() if order.cancelled_at else None,
                'line_items': line_items_data,
                'tags': order.tags,
                'note': order.note,
            })
        
        # Calculate customer statistics
        all_customer_orders = ShopifyOrder.objects.filter(customer_email=customer_email)
        stats = all_customer_orders.aggregate(
            total_orders=Count('id'),
            pending_orders=Count('id', filter=Q(financial_status='pending')),
            paid_orders=Count('id', filter=Q(financial_status='paid')),
            fulfilled_orders=Count('id', filter=Q(fulfillment_status='fulfilled')),
            cancelled_orders=Count('id', filter=Q(financial_status='cancelled')),
            total_spent=Sum('total_price')
        )
        
        customer_stats = {
            'total_orders': stats['total_orders'],
            'pending_orders': stats['pending_orders'],
            'paid_orders': stats['paid_orders'],
            'fulfilled_orders': stats['fulfilled_orders'],
            'cancelled_orders': stats['cancelled_orders'],
            'total_spent': float(stats['total_spent'] or 0),
        }
        
        return Response({
            'success': True,
            'orders': orders_data,
            'pagination': {
                'total_orders': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'statistics': customer_stats
        })
        
    except Exception as e:
        logger.error(f"Error in customer_orders: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to retrieve customer orders',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_cancel(request, shopify_id):
    """
    Cancel an order
    
    POST Data:
    {
        "reason": "Customer requested cancellation"
    }
    """
    try:
        order = get_object_or_404(ShopifyOrder, shopify_id=shopify_id)
        
        # Check if order can be cancelled
        if order.financial_status not in ['pending']:
            return Response({
                'success': False,
                'error': 'Order cannot be cancelled. Only pending orders can be cancelled.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if order.fulfillment_status in ['fulfilled', 'partial']:
            return Response({
                'success': False,
                'error': 'Order cannot be cancelled. It has already been fulfilled.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cancellation reason
        reason = request.data.get('reason', 'Customer requested cancellation')
        
        # Cancel order via Shopify API
        client = ShopifyAPIClient()
        result = client.cancel_order(shopify_id, reason)
        
        if result and 'order' in result:
            cancelled_order = result['order']
            
            # Update local order status
            order.financial_status = 'cancelled'
            order.cancelled_at = parse_datetime(cancelled_order.get('cancelled_at'))
            order.save()
            
            return Response({
                'success': True,
                'message': 'Order cancelled successfully',
                'order': {
                    'id': order.id,
                    'shopify_id': order.shopify_id,
                    'name': order.name,
                    'financial_status': order.financial_status,
                    'cancelled_at': order.cancelled_at.isoformat() if order.cancelled_at else None,
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to cancel order in Shopify',
                'details': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error in order_cancel: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to cancel order',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_invoice(request, shopify_id):
    """
    Generate and download order invoice PDF
    """
    try:
        order = get_object_or_404(ShopifyOrder, shopify_id=shopify_id)
        
        # Generate PDF invoice (this would need to be implemented)
        # For now, return a placeholder response
        
        from django.http import HttpResponse
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            import io
        except ImportError:
            return Response({
                'success': False,
                'error': 'PDF generation not available. Please install reportlab.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.setFont("Helvetica-Bold", 16)
        p.drawString(72, 750, f"Invoice - {order.name}")
        
        p.setFont("Helvetica", 12)
        p.drawString(72, 720, f"Date: {order.created_at.strftime('%B %d, %Y') if order.created_at else 'N/A'}")
        p.drawString(72, 700, f"Customer: {order.customer_email}")
        p.drawString(72, 680, f"Status: {order.financial_status}")
        
        # Add line items
        y_position = 650
        p.setFont("Helvetica-Bold", 12)
        p.drawString(72, y_position, "Items:")
        
        y_position -= 20
        p.setFont("Helvetica", 10)
        for line_item in order.line_items.all():
            p.drawString(72, y_position, f"{line_item.title} - Qty: {line_item.quantity} - ${line_item.price}")
            y_position -= 15
            if y_position < 100:  # Start new page if needed
                p.showPage()
                y_position = 750
        
        # Add total
        y_position -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(72, y_position, f"Total: ${order.total_price} {order.currency_code}")
        
        p.save()
        
        # Get PDF value
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Create HTTP response
        response = HttpResponse(pdf_value, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice-{order.name}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error in order_invoice: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to generate invoice',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_update_address(request, shopify_id):
    """
    Update shipping address for an order (only if unfulfilled)
    
    POST Data:
    {
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Inc",
        "address1": "123 Main St",
        "address2": "Apt 4B",
        "city": "New York",
        "province": "NY",
        "country": "US",
        "zip": "10001",
        "phone": "555-123-4567"
    }
    """
    try:
        order = get_object_or_404(ShopifyOrder, shopify_id=shopify_id)
        
        # Check if order can be updated
        if order.fulfillment_status in ['fulfilled', 'partial']:
            return Response({
                'success': False,
                'error': 'Order address cannot be updated. Order has already been fulfilled.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get address data
        address_data = request.data
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'address1', 'city', 'country', 'zip']
        for field in required_fields:
            if not address_data.get(field):
                return Response({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update shipping address via Shopify API
        client = ShopifyAPIClient()
        
        shipping_address = {
            'first_name': address_data['first_name'],
            'last_name': address_data['last_name'],
            'company': address_data.get('company', ''),
            'address1': address_data['address1'],
            'address2': address_data.get('address2', ''),
            'city': address_data['city'],
            'province': address_data.get('province', ''),
            'country': address_data['country'],
            'zip': address_data['zip'],
            'phone': address_data.get('phone', ''),
        }
        
        result = client.update_order_address(shopify_id, shipping_address)
        
        if result and 'order' in result:
            updated_order = result['order']
            
            # Update local address
            shipping_address_obj, created = ShopifyOrderAddress.objects.update_or_create(
                order=order,
                address_type='shipping',
                defaults={
                    'first_name': address_data['first_name'],
                    'last_name': address_data['last_name'],
                    'company': address_data.get('company', ''),
                    'address1': address_data['address1'],
                    'address2': address_data.get('address2', ''),
                    'city': address_data['city'],
                    'province': address_data.get('province', ''),
                    'country': address_data['country'],
                    'zip_code': address_data['zip'],
                    'phone': address_data.get('phone', ''),
                    'store_domain': order.store_domain,
                    'last_synced': datetime.now(),
                }
            )
            
            return Response({
                'success': True,
                'message': 'Shipping address updated successfully',
                'address': {
                    'first_name': shipping_address_obj.first_name,
                    'last_name': shipping_address_obj.last_name,
                    'company': shipping_address_obj.company,
                    'address1': shipping_address_obj.address1,
                    'address2': shipping_address_obj.address2,
                    'city': shipping_address_obj.city,
                    'province': shipping_address_obj.province,
                    'country': shipping_address_obj.country,
                    'zip_code': shipping_address_obj.zip_code,
                    'phone': shipping_address_obj.phone,
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to update address in Shopify',
                'details': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error in order_update_address: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to update shipping address',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_status(request, shopify_id):
    """
    Get real-time order status and timeline events
    """
    try:
        order = get_object_or_404(ShopifyOrder, shopify_id=shopify_id)
        
        # Get timeline events from Shopify
        client = ShopifyAPIClient()
        events = client.get_order_events(shopify_id)
        
        # Build timeline
        timeline_events = []
        
        # Order placed event
        timeline_events.append({
            'id': 'order-placed',
            'title': 'Order Placed',
            'description': 'Your order has been received and is being processed',
            'date': order.created_at.strftime('%B %d, %Y at %I:%M %p') if order.created_at else '',
            'completed': True,
        })
        
        # Payment confirmed
        if order.financial_status == 'paid':
            timeline_events.append({
                'id': 'payment-confirmed',
                'title': 'Payment Confirmed',
                'description': 'Your payment has been successfully processed',
                'date': order.processed_at.strftime('%B %d, %Y at %I:%M %p') if order.processed_at else '',
                'completed': True,
            })
        
        # Order shipped
        if order.fulfillment_status == 'fulfilled':
            timeline_events.append({
                'id': 'order-shipped',
                'title': 'Order Shipped',
                'description': 'Your order has been shipped and is on its way',
                'date': order.updated_at.strftime('%B %d, %Y at %I:%M %p') if order.updated_at else '',
                'completed': True,
            })
        
        # Add Shopify events
        for event in events:
            if event.get('message'):
                timeline_events.append({
                    'id': f"shopify-event-{event.get('id', 'unknown')}",
                    'title': event.get('verb', '').title(),
                    'description': event.get('message', ''),
                    'date': event.get('createdAt', ''),
                    'completed': True,
                })
        
        # Sort by date
        timeline_events.sort((a, b) => new Date(a.date) - new Date(b.date))
        
        # Check if status changed
        status_changed = request.GET.get('last_status') != order.financial_status
        
        return Response({
            'success': True,
            'financial_status': order.financial_status,
            'fulfillment_status': order.fulfillment_status,
            'financial_status_label': order.get_financial_status_display(),
            'fulfillment_status_label': order.get_fulfillment_status_display(),
            'status_changed': status_changed,
            'timeline_events': timeline_events,
        })
        
    except Exception as e:
        logger.error(f"Error in order_status: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to get order status',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
