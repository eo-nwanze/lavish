from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """List all orders"""
    return Response({'orders': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, shopify_id):
    """Get order details"""
    return Response({'order': {}})
