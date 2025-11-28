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
