from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carrier_service_list(request):
    """List carrier services"""
    return Response({'carrier_services': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fulfillment_order_list(request):
    """List fulfillment orders"""
    return Response({'fulfillment_orders': []})
