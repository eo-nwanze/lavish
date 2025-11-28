from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_list(request):
    """List all products"""
    return Response({'products': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_detail(request, shopify_id):
    """Get product details"""
    return Response({'product': {}})
