"""
Enhanced Shopify API Client based on proven 7fa66cac patterns
Supports real-time data synchronization with pagination and comprehensive error handling
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger('shopify_integration')


class EnhancedShopifyAPIClient:
    """
    Enhanced Shopify API client based on proven 7fa66cac patterns
    Supports real-time data synchronization with pagination and error handling
    """
    
    def __init__(self, shop_domain: str = None, access_token: str = None, api_version: str = None):
        self.shop_domain = shop_domain or settings.SHOPIFY_STORE_URL
        self.access_token = access_token or settings.SHOPIFY_ACCESS_TOKEN
        self.api_version = api_version or settings.SHOPIFY_API_VERSION
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"
        self.graphql_endpoint = f"{self.base_url}/graphql.json"
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Admin API requests"""
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def execute_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query against Shopify Admin API with enhanced error handling"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        try:
            response = requests.post(
                self.graphql_endpoint,
                headers=self.get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"GraphQL request failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            
            result = response.json()
            
            if 'errors' in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                return result
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    # ==================== CUSTOMER QUERIES ====================
    
    def create_customers_query(self, first: int = 50, after: Optional[str] = None) -> str:
        """Create GraphQL query to fetch customers with pagination"""
        after_clause = f', after: "{after}"' if after else ""
        
        query = f"""
        query CustomerList {{
            customers(first: {first}{after_clause}) {{
                nodes {{
                    id
                    firstName
                    lastName
                    email
                    phone
                    createdAt
                    updatedAt
                    numberOfOrders
                    state
                    verifiedEmail
                    taxExempt
                    tags
                    addresses {{
                        id
                        firstName
                        lastName
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        phone
                        name
                        provinceCode
                        countryCodeV2
                    }}
                    defaultAddress {{
                        id
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        phone
                        provinceCode
                        countryCodeV2
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
        """
        return query.strip()
    
    def fetch_all_customers(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch all customers using pagination"""
        all_customers = []
        has_next_page = True
        cursor = None
        page_count = 0
        
        logger.info("Starting customer data retrieval...")
        
        while has_next_page:
            page_count += 1
            logger.info(f"Fetching customers page {page_count}...")
            
            query = self.create_customers_query(50, cursor)
            
            try:
                response = self.execute_graphql_query(query)
                
                if "errors" in response:
                    logger.error(f"GraphQL errors: {response['errors']}")
                    break
                
                customers_data = response.get("data", {}).get("customers", {})
                customers = customers_data.get("nodes", [])
                page_info = customers_data.get("pageInfo", {})
                
                all_customers.extend(customers)
                logger.info(f"Retrieved {len(customers)} customers from page {page_count}")
                
                # Check if there are more pages
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
                # Check if we've reached the limit
                if limit and len(all_customers) >= limit:
                    all_customers = all_customers[:limit]
                    logger.info(f"Reached specified limit of {limit} customers")
                    break
                
                if not has_next_page:
                    logger.info("Reached end of customer data")
                    
            except Exception as e:
                logger.error(f"Error fetching customers page {page_count}: {e}")
                break
        
        logger.info(f"Total customers retrieved: {len(all_customers)}")
        return all_customers

    # ==================== PRODUCT QUERIES ====================
    
    def create_products_query(self, first: int = 50, after: Optional[str] = None) -> str:
        """Create GraphQL query to fetch products with pagination"""
        after_clause = f', after: "{after}"' if after else ""
        
        query = f"""
        query GetProducts {{
            products(first: {first}{after_clause}) {{
                nodes {{
                    id
                    title
                    handle
                    description
                    vendor
                    productType
                    status
                    createdAt
                    updatedAt
                    publishedAt
                    tags
                    totalInventory
                    tracksInventory
                    variants(first: 10) {{
                        edges {{
                            node {{
                                id
                                title
                                sku
                                price
                                compareAtPrice
                                inventoryQuantity
                                inventoryItem {{
                                    id
                                    tracked
                                }}
                            }}
                        }}
                    }}
                    images(first: 5) {{
                        edges {{
                            node {{
                                id
                                src
                                altText
                            }}
                        }}
                    }}
                    seo {{
                        title
                        description
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
        """
        return query.strip()
    
    def fetch_all_products(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch all products using pagination"""
        all_products = []
        has_next_page = True
        cursor = None
        page_count = 0
        
        logger.info("Starting products retrieval...")
        
        while has_next_page:
            page_count += 1
            logger.info(f"Fetching products page {page_count}...")
            
            query = self.create_products_query(50, cursor)
            
            try:
                response = self.execute_graphql_query(query)
                
                if "errors" in response:
                    logger.error(f"GraphQL errors: {response['errors']}")
                    break
                
                products_data = response.get("data", {}).get("products", {})
                products = products_data.get("nodes", [])
                page_info = products_data.get("pageInfo", {})
                
                all_products.extend(products)
                logger.info(f"Retrieved {len(products)} products from page {page_count}")
                
                # Check if there are more pages
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
                # Check if we've reached the limit
                if limit and len(all_products) >= limit:
                    all_products = all_products[:limit]
                    logger.info(f"Reached specified limit of {limit} products")
                    break
                
                if not has_next_page:
                    logger.info("Reached end of products")
                    
            except Exception as e:
                logger.error(f"Error fetching products page {page_count}: {e}")
                break
        
        logger.info(f"Total products retrieved: {len(all_products)}")
        return all_products

    # ==================== ORDER QUERIES ====================
    
    def create_orders_query(self, first: int = 50, after: Optional[str] = None) -> str:
        """Create GraphQL query to fetch orders with pagination"""
        after_clause = f', after: "{after}"' if after else ""
        
        query = f"""
        query OrdersList {{
            orders(first: {first}{after_clause}) {{
                edges {{
                    cursor
                    node {{
                        id
                        name
                        email
                        createdAt
                        updatedAt
                        totalPriceSet {{
                            shopMoney {{
                                amount
                                currencyCode
                            }}
                        }}
                        displayFulfillmentStatus
                        displayFinancialStatus
                        processedAt
                        tags
                        note
                        customer {{
                            id
                            firstName
                            lastName
                            email
                        }}
                        shippingAddress {{
                            firstName
                            lastName
                            address1
                            city
                            province
                            country
                            zip
                        }}
                        lineItems(first: 20) {{
                            edges {{
                                node {{
                                    id
                                    title
                                    quantity
                                    variant {{
                                        id
                                        title
                                        sku
                                        price
                                    }}
                                    product {{
                                        id
                                        title
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
        """
        return query.strip()
    
    def fetch_all_orders(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch all orders using pagination"""
        all_orders = []
        has_next_page = True
        cursor = None
        page_count = 0
        
        logger.info("Starting orders retrieval...")
        
        while has_next_page:
            page_count += 1
            logger.info(f"Fetching orders page {page_count}...")
            
            query = self.create_orders_query(50, cursor)
            
            try:
                response = self.execute_graphql_query(query)
                
                if "errors" in response:
                    logger.error(f"GraphQL errors: {response['errors']}")
                    break
                
                orders_data = response.get("data", {}).get("orders", {})
                edges = orders_data.get("edges", [])
                orders = [edge["node"] for edge in edges]
                page_info = orders_data.get("pageInfo", {})
                
                all_orders.extend(orders)
                logger.info(f"Retrieved {len(orders)} orders from page {page_count}")
                
                # Check if there are more pages
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
                # Check if we've reached the limit
                if limit and len(all_orders) >= limit:
                    all_orders = all_orders[:limit]
                    logger.info(f"Reached specified limit of {limit} orders")
                    break
                
                if not has_next_page:
                    logger.info("Reached end of orders")
                    
            except Exception as e:
                logger.error(f"Error fetching orders page {page_count}: {e}")
                break
        
        logger.info(f"Total orders retrieved: {len(all_orders)}")
        return all_orders

    # ==================== INVENTORY QUERIES ====================
    
    def create_inventory_items_query(self, first: int = 50, after: Optional[str] = None) -> str:
        """Create GraphQL query to fetch inventory items with pagination"""
        after_clause = f', after: "{after}"' if after else ""
        
        query = f"""
        query GetInventoryItems {{
            inventoryItems(first: {first}{after_clause}) {{
                edges {{
                    node {{
                        id
                        sku
                        tracked
                        requiresShipping
                        createdAt
                        updatedAt
                        unitCost {{
                            amount
                        }}
                        countryCodeOfOrigin
                        provinceCodeOfOrigin
                        harmonizedSystemCode
                        inventoryLevels(first: 10) {{
                            edges {{
                                node {{
                                    id
                                    quantities(names: ["available"]) {{
                                        name
                                        quantity
                                    }}
                                    updatedAt
                                    location {{
                                        id
                                        name
                                    }}
                                }}
                            }}
                        }}
                        variant {{
                            id
                            title
                            price
                            inventoryQuantity
                            product {{
                                id
                                title
                            }}
                        }}
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
        """
        return query.strip()
    
    def fetch_all_inventory_items(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch all inventory items using pagination"""
        all_items = []
        has_next_page = True
        cursor = None
        page_count = 0
        
        logger.info("Starting inventory items retrieval...")
        
        while has_next_page:
            page_count += 1
            logger.info(f"Fetching inventory items page {page_count}...")
            
            query = self.create_inventory_items_query(50, cursor)
            
            try:
                response = self.execute_graphql_query(query)
                
                if "errors" in response:
                    logger.error(f"GraphQL errors: {response['errors']}")
                    break
                
                items_data = response.get("data", {}).get("inventoryItems", {})
                edges = items_data.get("edges", [])
                items = [edge["node"] for edge in edges]
                page_info = items_data.get("pageInfo", {})
                
                all_items.extend(items)
                logger.info(f"Retrieved {len(items)} inventory items from page {page_count}")
                
                # Check if there are more pages
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
                # Check if we've reached the limit
                if limit and len(all_items) >= limit:
                    all_items = all_items[:limit]
                    logger.info(f"Reached specified limit of {limit} inventory items")
                    break
                
                if not has_next_page:
                    logger.info("Reached end of inventory items")
                    
            except Exception as e:
                logger.error(f"Error fetching inventory items page {page_count}: {e}")
                break
        
        logger.info(f"Total inventory items retrieved: {len(all_items)}")
        return all_items
    
    def fetch_all_locations(self) -> List[Dict]:
        """Fetch all locations"""
        query = """
        query {
            locations(first: 10) {
                edges {
                    node {
                        id
                        name
                        isActive
                        address {
                            address1
                            address2
                            city
                            province
                            country
                            zip
                            phone
                        }
                    }
                }
            }
        }
        """
        
        try:
            response = self.execute_graphql_query(query)
            
            if 'errors' in response:
                logger.error(f"GraphQL errors: {response['errors']}")
                return []
            
            locations_data = response.get('data', {}).get('locations', {})
            edges = locations_data.get('edges', [])
            locations = [edge['node'] for edge in edges]
            
            logger.info(f"Retrieved {len(locations)} locations")
            return locations
            
        except Exception as e:
            logger.error(f"Error fetching locations: {e}")
            return []
    
    def fetch_all_inventory_levels(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch all inventory levels using pagination"""
        all_levels = []
        has_next_page = True
        cursor = None
        page_count = 0
        
        while has_next_page:
            page_count += 1
            after_clause = f', after: "{cursor}"' if cursor else ""
            page_size = min(50, limit - len(all_levels)) if limit else 50
            
            query = f"""
            query {{
                inventoryItems(first: {page_size}{after_clause}) {{
                    edges {{
                        node {{
                            id
                            inventoryLevels(first: 10) {{
                                edges {{
                                    node {{
                                        id
                                        item {{
                                            id
                                        }}
                                        location {{
                                            id
                                            name
                                        }}
                                        quantities(names: ["available"]) {{
                                            name
                                            quantity
                                        }}
                                        updatedAt
                                    }}
                                }}
                            }}
                        }}
                    }}
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                }}
            }}
            """
            
            try:
                response = self.execute_graphql_query(query)
                
                if 'errors' in response:
                    logger.error(f"GraphQL errors: {response['errors']}")
                    break
                
                items_data = response.get('data', {}).get('inventoryItems', {})
                edges = items_data.get('edges', [])
                
                # Extract inventory levels from items
                for edge in edges:
                    item_node = edge.get('node', {})
                    level_edges = item_node.get('inventoryLevels', {}).get('edges', [])
                    
                    for level_edge in level_edges:
                        level = level_edge.get('node', {})
                        if level:
                            all_levels.append(level)
                
                page_info = items_data.get('pageInfo', {})
                has_next_page = page_info.get('hasNextPage', False)
                cursor = page_info.get('endCursor')
                
                if limit and len(all_levels) >= limit:
                    break
                
                if not has_next_page or not cursor:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching inventory levels page {page_count}: {e}")
                break
        
        logger.info(f"Retrieved {len(all_levels)} inventory levels")
        return all_levels

    # ==================== UTILITY METHODS ====================
    
    def test_connection(self) -> Dict:
        """Test the API connection with a simple shop query"""
        query = """
        query {
            shop {
                name
                email
                myshopifyDomain
                currencyCode
            }
        }
        """
        
        try:
            response = self.execute_graphql_query(query)
            
            if 'errors' in response:
                return {
                    'success': False,
                    'error': response['errors'],
                    'message': 'GraphQL errors in connection test'
                }
            
            if 'data' in response and 'shop' in response['data']:
                shop_data = response['data']['shop']
                return {
                    'success': True,
                    'shop_info': shop_data,
                    'message': f"Successfully connected to {shop_data.get('name', 'Unknown Store')}"
                }
            
            return {
                'success': False,
                'error': 'No shop data in response',
                'message': 'Invalid response structure'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Connection test failed: {e}'
            }
    
    def get_shop_info(self) -> Dict:
        """Get basic shop information"""
        connection_test = self.test_connection()
        if connection_test['success']:
            return connection_test['shop_info']
        else:
            raise Exception(f"Failed to get shop info: {connection_test['message']}")
    
    # ==================== PRODUCT MUTATIONS (Django → Shopify) ====================
    
    def create_product_in_shopify(self, title: str, description: str = "", vendor: str = "", 
                                   product_type: str = "", tags: List[str] = None,
                                   variants: List[Dict] = None, images: List[Dict] = None,
                                   status: str = "DRAFT") -> Dict:
        """
        Create a new product in Shopify from Django
        
        Args:
            title: Product title
            description: Product description (HTML supported)
            vendor: Product vendor/brand
            product_type: Product type/category
            tags: List of tags
            variants: List of variant dicts with price, sku, inventory_quantity, etc.
            images: List of image dicts with src URLs
            status: ACTIVE, DRAFT, or ARCHIVED
            
        Returns:
            Dict with success status, product data, and any errors
        """
        mutation = """
        mutation productCreate($input: ProductInput!) {
          productCreate(input: $input) {
            product {
              id
              title
              handle
              descriptionHtml
              vendor
              productType
              tags
              status
              createdAt
              updatedAt
              variants(first: 100) {
                edges {
                  node {
                    id
                    title
                    price
                    sku
                    inventoryQuantity
                  }
                }
              }
              images(first: 100) {
                edges {
                  node {
                    id
                    url
                    altText
                  }
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        # Build product input (NOTE: ProductInput does NOT accept variants directly!)
        product_input = {
            "title": title,
            "descriptionHtml": description,
            "vendor": vendor or "",
            "productType": product_type or "",
            "status": status.upper(),
        }
        
        if tags:
            product_input["tags"] = tags
        
        # Add images if provided
        if images:
            product_input["images"] = []
            for image in images:
                if "src" in image:
                    product_input["images"].append({
                        "src": image["src"],
                        "altText": image.get("alt", "")
                    })
        
        variables = {"input": product_input}
        
        try:
            result = self.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"Product creation failed: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            product_data = result.get("data", {}).get("productCreate", {})
            user_errors = product_data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Product creation validation errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            product = product_data.get("product")
            if product:
                product_id = product['id']
                logger.info(f"Successfully created product in Shopify: {product_id}")
                
                # Shopify automatically creates a default variant - we just need to sync it back to Django
                # The variant will have a proper Shopify ID that we can use
                
                return {
                    "success": True,
                    "product": product,
                    "message": f"Product '{title}' created successfully"
                }
            
            return {
                "success": False,
                "message": "No product data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception creating product: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create product: {e}"
            }
    
    def update_product_in_shopify(self, shopify_product_id: str, title: str = None,
                                   description: str = None, vendor: str = None,
                                   product_type: str = None, tags: List[str] = None,
                                   status: str = None) -> Dict:
        """
        Update an existing product in Shopify
        
        Args:
            shopify_product_id: Shopify GID (e.g., gid://shopify/Product/123456)
            title: New product title
            description: New product description
            vendor: New vendor
            product_type: New product type
            tags: New tags list
            status: New status (ACTIVE, DRAFT, ARCHIVED)
            
        Returns:
            Dict with success status and updated product data
        """
        mutation = """
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product {
              id
              title
              handle
              descriptionHtml
              vendor
              productType
              tags
              status
              updatedAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        # Build update input - only include fields that are provided
        product_input = {"id": shopify_product_id}
        
        if title is not None:
            product_input["title"] = title
        if description is not None:
            product_input["descriptionHtml"] = description
        if vendor is not None:
            product_input["vendor"] = vendor
        if product_type is not None:
            product_input["productType"] = product_type
        if tags is not None:
            product_input["tags"] = tags
        if status is not None:
            product_input["status"] = status.upper()
        
        variables = {"input": product_input}
        
        try:
            result = self.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            product_data = result.get("data", {}).get("productUpdate", {})
            user_errors = product_data.get("userErrors", [])
            
            if user_errors:
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            product = product_data.get("product")
            if product:
                logger.info(f"Successfully updated product in Shopify: {product['id']}")
                return {
                    "success": True,
                    "product": product,
                    "message": f"Product updated successfully"
                }
            
            return {
                "success": False,
                "message": "No product data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception updating product: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update product: {e}"
            }
    
    def delete_product_in_shopify(self, shopify_product_id: str) -> Dict:
        """
        Delete a product from Shopify
        
        Args:
            shopify_product_id: Shopify GID (e.g., gid://shopify/Product/123456)
            
        Returns:
            Dict with success status
        """
        mutation = """
        mutation productDelete($input: ProductDeleteInput!) {
          productDelete(input: $input) {
            deletedProductId
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "id": shopify_product_id
            }
        }
        
        try:
            result = self.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            product_data = result.get("data", {}).get("productDelete", {})
            user_errors = product_data.get("userErrors", [])
            
            if user_errors:
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            deleted_id = product_data.get("deletedProductId")
            if deleted_id:
                logger.info(f"Successfully deleted product from Shopify: {deleted_id}")
                return {
                    "success": True,
                    "deleted_id": deleted_id,
                    "message": "Product deleted successfully"
                }
            
            return {
                "success": False,
                "message": "No deletion confirmation in response"
            }
            
        except Exception as e:
            logger.error(f"Exception deleting product: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete product: {e}"
            }
    
    def _update_product_variant(self, variant_id: str, price: str = None, 
                                sku: str = None, inventory_quantity: int = None) -> Dict:
        """
        Update a product variant
        
        Args:
            variant_id: Shopify variant GID
            price: Variant price
            sku: Variant SKU
            inventory_quantity: Inventory quantity
            
        Returns:
            Dict with success status
        """
        mutation = """
        mutation productVariantUpdate($input: ProductVariantInput!) {
          productVariantUpdate(input: $input) {
            productVariant {
              id
              price
              sku
              inventoryQuantity
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variant_input = {"id": variant_id}
        
        if price is not None:
            variant_input["price"] = str(price)
        if sku is not None:
            variant_input["sku"] = sku
        if inventory_quantity is not None:
            variant_input["inventoryQuantities"] = {
                "availableQuantity": int(inventory_quantity),
                "locationId": "gid://shopify/Location/PRIMARY"
            }
        
        variables = {"input": variant_input}
        
        try:
            result = self.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            variant_data = result.get("data", {}).get("productVariantUpdate", {})
            user_errors = variant_data.get("userErrors", [])
            
            if user_errors:
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            variant = variant_data.get("productVariant")
            if variant:
                return {
                    "success": True,
                    "variant": variant,
                    "message": "Variant updated successfully"
                }
            
            return {
                "success": False,
                "message": "No variant data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception updating variant: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update variant: {e}"
            }
    
    def _create_product_variant(self, product_id: str, price: str = "0.00",
                                sku: str = "", inventory_quantity: int = 0,
                                title: str = "Default") -> Dict:
        """
        Create a new product variant
        
        Args:
            product_id: Shopify product GID
            price: Variant price
            sku: Variant SKU
            inventory_quantity: Inventory quantity
            title: Variant title
            
        Returns:
            Dict with success status
        """
        mutation = """
        mutation productVariantCreate($input: ProductVariantInput!) {
          productVariantCreate(input: $input) {
            productVariant {
              id
              title
              price
              sku
              inventoryQuantity
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variant_input = {
            "productId": product_id,
            "price": str(price),
            "sku": sku,
            "options": [title]
        }
        
        if inventory_quantity > 0:
            variant_input["inventoryQuantities"] = {
                "availableQuantity": int(inventory_quantity),
                "locationId": "gid://shopify/Location/PRIMARY"
            }
        
        variables = {"input": variant_input}
        
        try:
            result = self.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            variant_data = result.get("data", {}).get("productVariantCreate", {})
            user_errors = variant_data.get("userErrors", [])
            
            if user_errors:
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            variant = variant_data.get("productVariant")
            if variant:
                return {
                    "success": True,
                    "variant": variant,
                    "message": "Variant created successfully"
                }
            
            return {
                "success": False,
                "message": "No variant data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception creating variant: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create variant: {e}"
            }
    
    def update_inventory_quantities(self, inventory_item_id: str, available_quantity: int, location_id: str = None) -> Dict:
        """
        Update inventory quantities for a variant using inventorySetQuantities mutation
        
        Args:
            inventory_item_id: Shopify inventory item ID (get from variant.inventoryItem.id)
            available_quantity: The quantity to set
            location_id: Location ID (defaults to primary location if not provided)
            
        Returns:
            Dict with success status
        """
        # Get primary location if not provided
        if not location_id:
            location_query = """
            {
              locations(first: 1) {
                edges {
                  node {
                    id
                  }
                }
              }
            }
            """
            loc_result = self.execute_graphql_query(location_query)
            locations = loc_result.get("data", {}).get("locations", {}).get("edges", [])
            if locations:
                location_id = locations[0]["node"]["id"]
            else:
                return {
                    "success": False,
                    "message": "No location found in Shopify"
                }
        
        mutation = """
        mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
          inventorySetQuantities(input: $input) {
            inventoryAdjustmentGroup {
              id
              reason
              changes {
                name
                delta
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "reason": "correction",
                "name": "available",
                "ignoreCompareQuantity": True,
                "quantities": [
                    {
                        "inventoryItemId": inventory_item_id,
                        "locationId": location_id,
                        "quantity": int(available_quantity)
                    }
                ]
            }
        }
        
        try:
            result = self.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"GraphQL errors updating inventory: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            inventory_data = result.get("data", {}).get("inventorySetQuantities", {})
            user_errors = inventory_data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Inventory update validation errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            adjustment = inventory_data.get("inventoryAdjustmentGroup")
            if adjustment:
                return {
                    "success": True,
                    "adjustment": adjustment,
                    "message": "Inventory updated successfully"
                }
            
            return {
                "success": False,
                "message": "No adjustment data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception updating inventory: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update inventory: {e}"
            }

