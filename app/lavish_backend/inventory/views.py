from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_item_list(request):
    """List inventory items"""
    return Response({'inventory_items': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_level_list(request):
    """List inventory levels"""
    return Response({'inventory_levels': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def location_list(request):
    """List locations"""
    return Response({'locations': []})
