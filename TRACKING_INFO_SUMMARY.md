# Tracking Info System - Complete Summary

## Current Status ✅

### What's Been Implemented:
1. **FulfillmentTrackingInfo Model** - Stores tracking data from Shopify
2. **Fulfillment Order Sync** - Syncs fulfillment orders from Shopify orders
3. **Admin Interface** - View and manage tracking info in Django admin
4. **Auto-URL Generation** - Automatically creates tracking URLs for 10+ carriers

### Database Status (as of sync):
- **Orders**: 765
- **Fulfillment Orders**: 20 (synced from Shopify)
- **Tracking Info Records**: 0 (none available yet in Shopify)

---

## How Tracking Info Links to Orders

### The Relationship Chain:
```
ShopifyOrder (765 orders)
    ↓
ShopifyFulfillmentOrder (20 fulfillment orders)
    ↓
FulfillmentTrackingInfo (0 tracking records)
```

### Explanation:

1. **ShopifyOrder** = The customer's order in your store
   - Contains order details, customer info, line items, totals
   - Example: Order #1728, #1727, etc.

2. **ShopifyFulfillmentOrder** = The logistics/shipping instruction for an order
   - Each order can have multiple fulfillment orders (split shipments)
   - Contains status: `open`, `in_progress`, `closed`
   - Links to location where items will ship from
   - **Currently: 20 fulfillment orders, all status = "open"**

3. **FulfillmentTrackingInfo** = The actual tracking number from the carrier
   - Links to a fulfillment order
   - Contains: carrier company, tracking number, tracking URL
   - **Only exists AFTER an order is shipped by the merchant**
   - **Currently: 0 records (no orders shipped yet)**

---

## Why Tracking Info is Empty

### The 20 fulfillment orders are all status "open", which means:
- ❌ Not yet shipped by the merchant
- ❌ No carrier assigned yet
- ❌ No tracking number generated
- ❌ No tracking URL available

### When will tracking info appear?
Tracking info will be created when:
1. Merchant fulfills an order in Shopify admin
2. Merchant selects a carrier (FedEx, UPS, USPS, etc.)
3. Merchant enters tracking number
4. Shopify creates tracking info in the order's fulfillments
5. Next sync pulls that tracking data into Django

---

## How to Sync Tracking Info

### Command:
```bash
python manage.py sync_shipping_data --fulfillment-orders
```

### What it does:
1. Queries Shopify for orders with fulfillment status (not null)
2. For each order, fetches fulfillment orders (up to 10)
3. For each order, fetches fulfillments with tracking info
4. Creates/updates `ShopifyFulfillmentOrder` records
5. Creates/updates `FulfillmentTrackingInfo` records (if tracking exists)

### Batch size:
- Currently syncs **20 orders at a time** to avoid API timeouts
- Can run multiple times to sync more orders
- Has 500ms delay between requests to respect API limits

---

## Viewing Tracking Info in Admin

### Admin URLs:
- **Fulfillment Orders**: `http://localhost:8003/admin/shipping/shopifyfulfillmentorder/`
- **Tracking Info**: `http://localhost:8003/admin/shipping/fulfillmenttrackinginfo/`

### What you'll see:
- Fulfillment orders with status, location, timestamps
- Tracking info with clickable tracking links (when available)
- Auto-generated tracking URLs for supported carriers

---

## Supported Carriers (Auto-URL Generation)

The system automatically generates tracking URLs for:
1. **FedEx** → `https://www.fedex.com/fedextrack/?trknbr={number}`
2. **UPS** → `https://www.ups.com/track?tracknum={number}`
3. **USPS** → `https://tools.usps.com/go/TrackConfirmAction?tLabels={number}`
4. **DHL Express** → `https://www.dhl.com/en/express/tracking.html?AWB={number}`
5. **DHL eCommerce** → `https://www.dhl.com/en/express/tracking.html?AWB={number}`
6. **Canada Post** → `https://www.canadapost-postescanada.ca/track-reperage/en#/search?searchFor={number}`
7. **Australia Post** → `https://auspost.com.au/mypost/track/#/details/{number}`
8. **Royal Mail** → `https://www.royalmail.com/track-your-item#/tracking-results/{number}`
9. **Purolator** → `https://www.purolator.com/en/ship-track/tracking-details.page?pin={number}`
10. **Sendle** → `https://track.sendle.com/{number}`

If carrier provides a custom URL, that's used instead of auto-generation.

---

## Testing the System

### 1. Fulfill an Order in Shopify:
- Go to Shopify Admin → Orders
- Select an order
- Click "Fulfill items"
- Select carrier and enter tracking number
- Click "Fulfill"

### 2. Sync Tracking Info:
```bash
python manage.py sync_shipping_data --fulfillment-orders
```

### 3. Verify in Django Admin:
- Go to: `http://localhost:8003/admin/shipping/fulfillmenttrackinginfo/`
- You should see the new tracking record
- Click the "🔗 Track Shipment" link to test URL

---

## API Query Structure

### The GraphQL query fetches:
```graphql
query getFulfillmentOrders($orderId: ID!) {
    order(id: $orderId) {
        fulfillmentOrders {
            # Fulfillment order details
            id, status, requestStatus, fulfillAt, fulfillBy
            deliveryMethod { ... }
            assignedLocation { ... }
        }
        fulfillments {
            # THIS IS WHERE TRACKING INFO COMES FROM
            trackingInfo {
                company  # e.g., "FedEx"
                number   # e.g., "1234567890"
                url      # e.g., "https://fedex.com/track/..."
            }
        }
    }
}
```

### Key Point:
- **Fulfillment Orders** = logistics instructions (who, where, when)
- **Fulfillments** = actual shipments (carrier, tracking number)
- Tracking info lives in `fulfillments`, NOT in `fulfillmentOrders`

---

## Next Steps

### To get tracking data:
1. **Option A**: Fulfill test orders in Shopify with tracking numbers
2. **Option B**: Import historical fulfilled orders (they may have tracking)
3. **Option C**: Wait for new orders to be fulfilled by merchant

### To sync more orders:
```bash
# Run multiple times to sync all orders
python manage.py sync_shipping_data --fulfillment-orders
```

### To sync all shipping data at once:
```bash
# Syncs carriers, profiles, zones, methods, and rates (but not fulfillment orders by default)
python manage.py sync_shipping_data
```

---

## Summary

✅ **FulfillmentTrackingInfo model created** - Ready to store tracking data  
✅ **Fulfillment orders synced** - 20 orders from Shopify  
✅ **Admin interface ready** - Can view/manage tracking info  
✅ **Auto-URL generation working** - 10+ carriers supported  
⚠️ **No tracking data yet** - Orders not fulfilled/shipped in Shopify  

The system is **fully functional** and will populate tracking info as soon as orders are fulfilled in Shopify with tracking numbers.
