"""
Shopify Webhook Subscriptions API Client

Converted from Ruby to Python for managing webhook subscriptions via GraphQL Admin API.
"""

import os
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient


class ShopifyWebhooksClient:
    """
    Client for managing Shopify webhook subscriptions via GraphQL Admin API
    
    Ruby to Python conversion for webhook subscription management.
    """
    
    def __init__(self):
        """Initialize the webhooks client"""
        self.client = EnhancedShopifyAPIClient()
    
    def fetch_webhook_subscription(self, subscription_id):
        """
        Fetch a single webhook subscription by ID
        
        Ruby equivalent:
        query = <<~QUERY
          query {
            webhookSubscription(id: "gid://shopify/WebhookSubscription/892403750") {
              id
              topic
              uri
            }
          }
        QUERY
        response = client.query(query: query)
        
        Args:
            subscription_id: Shopify webhook subscription ID (e.g., "gid://shopify/WebhookSubscription/892403750")
            
        Returns:
            dict: GraphQL response with webhook subscription details
        """
        query = """
        query GetWebhookSubscription($id: ID!) {
            webhookSubscription(id: $id) {
                id
                topic
                endpoint {
                    __typename
                    ... on WebhookHttpEndpoint {
                        callbackUrl
                    }
                    ... on WebhookEventBridgeEndpoint {
                        arn
                    }
                    ... on WebhookPubSubEndpoint {
                        pubSubProject
                        pubSubTopic
                    }
                }
                format
                includeFields
                metafieldNamespaces
                createdAt
                updatedAt
                legacyResourceId
                apiVersion {
                    displayName
                    handle
                }
                filter
            }
        }
        """
        
        variables = {"id": subscription_id}
        return self.client.execute_graphql_query(query, variables)
    
    def fetch_webhook_subscriptions(self, first=50, after=None, topics=None):
        """
        Fetch webhook subscriptions with pagination
        
        Ruby equivalent:
        query = <<~QUERY
          query {
            webhookSubscriptions(first: 2) {
              edges {
                node {
                  id
                  topic
                  uri
                }
              }
            }
          }
        QUERY
        response = client.query(query: query)
        
        Args:
            first: Number of subscriptions to fetch (default: 50)
            after: Cursor for pagination
            topics: Optional list of topics to filter by
            
        Returns:
            dict: GraphQL response with webhook subscriptions
        """
        after_param = f', after: "{after}"' if after else ''
        topics_param = f', topics: {topics}' if topics else ''
        
        query = f"""
        query {{
            webhookSubscriptions(first: {first}{after_param}{topics_param}) {{
                edges {{
                    node {{
                        id
                        topic
                        endpoint {{
                            __typename
                            ... on WebhookHttpEndpoint {{
                                callbackUrl
                            }}
                            ... on WebhookEventBridgeEndpoint {{
                                arn
                            }}
                            ... on WebhookPubSubEndpoint {{
                                pubSubProject
                                pubSubTopic
                            }}
                        }}
                        format
                        includeFields
                        metafieldNamespaces
                        createdAt
                        updatedAt
                        legacyResourceId
                        apiVersion {{
                            displayName
                            handle
                        }}
                        filter
                    }}
                    cursor
                }}
                pageInfo {{
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }}
            }}
        }}
        """
        
        return self.client.execute_graphql_query(query)
    
    def fetch_all_webhook_subscriptions(self):
        """
        Fetch all webhook subscriptions with automatic pagination
        
        Returns:
            list: All webhook subscriptions
        """
        all_subscriptions = []
        has_next_page = True
        after = None
        
        while has_next_page:
            response = self.fetch_webhook_subscriptions(first=100, after=after)
            
            if 'data' in response and 'webhookSubscriptions' in response['data']:
                subscriptions_data = response['data']['webhookSubscriptions']
                
                for edge in subscriptions_data.get('edges', []):
                    all_subscriptions.append(edge['node'])
                    after = edge.get('cursor')
                
                page_info = subscriptions_data.get('pageInfo', {})
                has_next_page = page_info.get('hasNextPage', False)
            else:
                has_next_page = False
        
        return all_subscriptions
    
    def count_webhook_subscriptions(self, query_filter=None):
        """
        Count webhook subscriptions with optional filter
        
        Ruby equivalent:
        query = <<~QUERY
          query WebhookSubscriptionsCount($query: String!) {
            webhookSubscriptionsCount(query: $query) {
              count
              precision
            }
          }
        QUERY
        variables = {
          "query": "topic:\\"orders/create\\""
        }
        response = client.query(query: query, variables: variables)
        
        Args:
            query_filter: Optional query string (e.g., 'topic:"orders/create"')
            
        Returns:
            dict: Count and precision information
        """
        if query_filter:
            query = """
            query WebhookSubscriptionsCount($query: String!) {
                webhookSubscriptionsCount(query: $query) {
                    count
                    precision
                }
            }
            """
            variables = {"query": query_filter}
            return self.client.execute_graphql_query(query, variables)
        else:
            query = """
            query {
                webhookSubscriptionsCount {
                    count
                    precision
                }
            }
            """
            return self.client.execute_graphql_query(query)
    
    def create_webhook_subscription(self, topic, callback_url, format='JSON', include_fields=None, metafield_namespaces=None, filter_query=None):
        """
        Create a new webhook subscription
        
        Args:
            topic: Webhook topic (e.g., 'ORDERS_CREATE')
            callback_url: HTTPS URL to receive webhooks
            format: 'JSON' or 'XML' (default: 'JSON')
            include_fields: Optional list of fields to include
            metafield_namespaces: Optional list of metafield namespaces
            filter_query: Optional filter query
            
        Returns:
            dict: GraphQL response with created subscription
        """
        include_fields_param = f', includeFields: {include_fields}' if include_fields else ''
        metafield_param = f', metafieldNamespaces: {metafield_namespaces}' if metafield_namespaces else ''
        filter_param = f', filter: "{filter_query}"' if filter_query else ''
        
        mutation = f"""
        mutation {{
            webhookSubscriptionCreate(
                topic: {topic}
                webhookSubscription: {{
                    callbackUrl: "{callback_url}"
                    format: {format}
                    {include_fields_param}
                    {metafield_param}
                    {filter_param}
                }}
            ) {{
                webhookSubscription {{
                    id
                    topic
                    format
                    endpoint {{
                        __typename
                        ... on WebhookHttpEndpoint {{
                            callbackUrl
                        }}
                    }}
                    createdAt
                }}
                userErrors {{
                    field
                    message
                }}
            }}
        }}
        """
        
        return self.client.execute_graphql_query(mutation)
    
    def update_webhook_subscription(self, subscription_id, callback_url=None, include_fields=None, metafield_namespaces=None, filter_query=None):
        """
        Update an existing webhook subscription
        
        Args:
            subscription_id: Shopify webhook subscription ID
            callback_url: Optional new callback URL
            include_fields: Optional list of fields to include
            metafield_namespaces: Optional list of metafield namespaces
            filter_query: Optional filter query
            
        Returns:
            dict: GraphQL response with updated subscription
        """
        updates = []
        if callback_url:
            updates.append(f'callbackUrl: "{callback_url}"')
        if include_fields is not None:
            updates.append(f'includeFields: {include_fields}')
        if metafield_namespaces is not None:
            updates.append(f'metafieldNamespaces: {metafield_namespaces}')
        if filter_query is not None:
            updates.append(f'filter: "{filter_query}"')
        
        updates_str = ', '.join(updates)
        
        mutation = f"""
        mutation {{
            webhookSubscriptionUpdate(
                id: "{subscription_id}"
                webhookSubscription: {{
                    {updates_str}
                }}
            ) {{
                webhookSubscription {{
                    id
                    topic
                    format
                    endpoint {{
                        __typename
                        ... on WebhookHttpEndpoint {{
                            callbackUrl
                        }}
                    }}
                    updatedAt
                }}
                userErrors {{
                    field
                    message
                }}
            }}
        }}
        """
        
        return self.client.execute_graphql_query(mutation)
    
    def delete_webhook_subscription(self, subscription_id):
        """
        Delete a webhook subscription
        
        Args:
            subscription_id: Shopify webhook subscription ID
            
        Returns:
            dict: GraphQL response with deletion result
        """
        mutation = f"""
        mutation {{
            webhookSubscriptionDelete(id: "{subscription_id}") {{
                deletedWebhookSubscriptionId
                userErrors {{
                    field
                    message
                }}
            }}
        }}
        """
        
        return self.client.execute_graphql_query(mutation)
    
    def get_webhook_topics(self):
        """
        Get available webhook topics
        
        Returns:
            list: Available webhook topics
        """
        # Common webhook topics based on Shopify documentation
        return [
            'APP_UNINSTALLED',
            'CARTS_CREATE',
            'CARTS_UPDATE',
            'CHECKOUTS_CREATE',
            'CHECKOUTS_DELETE',
            'CHECKOUTS_UPDATE',
            'COLLECTIONS_CREATE',
            'COLLECTIONS_DELETE',
            'COLLECTIONS_UPDATE',
            'CUSTOMERS_CREATE',
            'CUSTOMERS_DELETE',
            'CUSTOMERS_DISABLE',
            'CUSTOMERS_ENABLE',
            'CUSTOMERS_UPDATE',
            'DISPUTES_CREATE',
            'DISPUTES_UPDATE',
            'FULFILLMENTS_CREATE',
            'FULFILLMENTS_UPDATE',
            'INVENTORY_ITEMS_CREATE',
            'INVENTORY_ITEMS_DELETE',
            'INVENTORY_ITEMS_UPDATE',
            'INVENTORY_LEVELS_CONNECT',
            'INVENTORY_LEVELS_DISCONNECT',
            'INVENTORY_LEVELS_UPDATE',
            'ORDERS_CANCELLED',
            'ORDERS_CREATE',
            'ORDERS_DELETE',
            'ORDERS_FULFILLED',
            'ORDERS_PAID',
            'ORDERS_PARTIALLY_FULFILLED',
            'ORDERS_UPDATED',
            'PRODUCTS_CREATE',
            'PRODUCTS_DELETE',
            'PRODUCTS_UPDATE',
            'REFUNDS_CREATE',
            'SHOP_UPDATE',
        ]
