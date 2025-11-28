"""
API Serializers for Shopify Data
Exposes Django backend data to Shopify theme frontend
"""

from rest_framework import serializers
from products.models import ShopifyProduct, ShopifyProductVariant, ShopifyProductImage
from inventory.models import ShopifyInventoryLevel, ShopifyInventoryItem, ShopifyLocation
from customers.models import ShopifyCustomer
from orders.models import ShopifyOrder, ShopifyOrderLineItem
from shipping.models import ShopifyCarrierService, ShopifyDeliveryMethod
from locations.models import Country, State, City


class CitySerializer(serializers.ModelSerializer):
    """Serializer for cities"""
    
    class Meta:
        model = City
        fields = ['id', 'name', 'latitude', 'longitude']


class StateSerializer(serializers.ModelSerializer):
    """Serializer for states with cities"""
    cities = CitySerializer(many=True, read_only=True)
    
    class Meta:
        model = State
        fields = ['id', 'name', 'state_code', 'cities']


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for countries with states"""
    states = StateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Country
        fields = ['id', 'name', 'iso_code', 'iso3_code', 'phone_code', 
                 'currency', 'currency_symbol', 'timezone', 'flag_emoji', 'states']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""
    
    class Meta:
        model = ShopifyProductImage
        fields = ['id', 'src', 'alt', 'position', 'width', 'height']


class InventoryLevelSerializer(serializers.ModelSerializer):
    """Serializer for inventory levels"""
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = ShopifyInventoryLevel
        fields = ['location_name', 'available', 'committed', 'incoming', 'on_hand']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants with inventory"""
    inventory_quantity = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopifyProductVariant
        fields = [
            'id', 'shopify_id', 'title', 'price', 'compare_at_price', 
            'sku', 'barcode', 'weight', 'weight_unit', 
            'inventory_quantity', 'in_stock', 'available'
        ]
    
    def get_inventory_quantity(self, obj):
        """Get total available inventory across all locations"""
        if hasattr(obj, 'inventory_item') and obj.inventory_item:
            levels = obj.inventory_item.levels.all()
            return sum(level.available for level in levels)
        return 0
    
    def get_in_stock(self, obj):
        """Check if product is in stock"""
        return self.get_inventory_quantity(obj) > 0


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    image_url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopifyProduct
        fields = [
            'id', 'shopify_id', 'title', 'handle', 'product_type', 
            'vendor', 'image_url', 'price', 'in_stock', 'status'
        ]
    
    def get_image_url(self, obj):
        """Get first product image"""
        image = obj.images.first()
        return image.src if image else None
    
    def get_price(self, obj):
        """Get price from first variant"""
        variant = obj.variants.first()
        return str(variant.price) if variant else "0.00"
    
    def get_in_stock(self, obj):
        """Check if any variant is in stock"""
        for variant in obj.variants.all():
            if hasattr(variant, 'inventory_item') and variant.inventory_item:
                levels = variant.inventory_item.levels.all()
                if sum(level.available for level in levels) > 0:
                    return True
        return False


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single product view"""
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = ShopifyProduct
        fields = [
            'id', 'shopify_id', 'title', 'handle', 'description', 
            'product_type', 'vendor', 'tags', 'status', 
            'images', 'variants', 'created_at', 'updated_at'
        ]


class CarrierServiceSerializer(serializers.ModelSerializer):
    """Serializer for shipping carriers"""
    
    class Meta:
        model = ShopifyCarrierService
        fields = ['id', 'name', 'active', 'service_discovery', 'carrier_service_type']


class DeliveryMethodSerializer(serializers.ModelSerializer):
    """Serializer for delivery methods"""
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    
    class Meta:
        model = ShopifyDeliveryMethod
        fields = ['id', 'name', 'zone_name', 'method_type']


class OrderLineItemSerializer(serializers.ModelSerializer):
    """Serializer for order line items"""
    
    class Meta:
        model = ShopifyOrderLineItem
        fields = ['id', 'name', 'quantity', 'price', 'sku', 'variant_title']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    line_items = OrderLineItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopifyOrder
        fields = [
            'id', 'shopify_id', 'order_number', 'email', 'total_price', 
            'subtotal_price', 'total_tax', 'financial_status', 
            'fulfillment_status', 'customer_name', 'line_items', 
            'created_at', 'updated_at'
        ]
    
    def get_customer_name(self, obj):
        """Get customer name"""
        if obj.customer:
            return f"{obj.customer.first_name} {obj.customer.last_name}".strip()
        return "Guest"


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for customers"""
    
    class Meta:
        model = ShopifyCustomer
        fields = [
            'id', 'shopify_id', 'email', 'first_name', 'last_name', 
            'phone', 'orders_count', 'total_spent', 'created_at'
        ]
