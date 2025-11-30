"""
Shopify Payments API Client
Converted from Ruby to Python for store: 7fa66c-ac.myshopify.com
"""

from shopify_integration.enhanced_client import EnhancedShopifyAPIClient


class ShopifyPaymentsClient:
    """Client for fetching Shopify Payments data"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    def fetch_balance_transactions(self, first=50, after=None):
        """
        Fetch balance transactions from Shopify Payments account
        
        Args:
            first: Number of transactions to fetch
            after: Cursor for pagination
            
        Returns:
            dict: GraphQL response with balance transactions
        """
        after_clause = f', after: "{after}"' if after else ''
        query = """
        query {
            shopifyPaymentsAccount {
                id
                activated
                country
                defaultCurrency
                onboardable
                payoutStatementDescriptor
                chargeStatementDescriptor
                balanceTransactions(first: """ + str(first) + after_clause + """) {
                    edges {
                        node {
                            id
                            type
                            test
                            associatedPayout {
                                id
                                status
                            }
                            amount {
                                amount
                                currencyCode
                            }
                            fee {
                                amount
                            }
                            net {
                                amount
                            }
                            sourceId
                            sourceType
                            sourceOrderTransactionId
                            associatedOrder {
                                id
                            }
                            adjustmentsOrders {
                                orderTransactionId
                                amount {
                                    amount
                                }
                                name
                            }
                            adjustmentReason
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        }
        """
        
        return self.client.execute_graphql_query(query)
    
    def fetch_payouts(self, first=50, after=None):
        """
        Fetch payouts from Shopify Payments account
        
        Args:
            first: Number of payouts to fetch
            after: Cursor for pagination
            
        Returns:
            dict: GraphQL response with payouts
        """
        after_part = f', after: "{after}"' if after else ''
        query = """
        query {
            shopifyPaymentsAccount {
                id
                payouts(first: """ + str(first) + after_part + """) {
                    edges {
                        node {
                            id
                            status
                            gross {
                                amount
                                currencyCode
                            }
                            net {
                                amount
                                currencyCode
                            }
                            bankAccount {
                                id
                                bankName
                                status
                            }
                            issuedAt
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        }
        """
        
        return self.client.execute_graphql_query(query)
    
    def fetch_disputes(self, first=50, after=None):
        """
        Fetch disputes from Shopify Payments account
        
        Args:
            first: Number of disputes to fetch
            after: Cursor for pagination
            
        Returns:
            dict: GraphQL response with disputes
        """
        after_part = f', after: "{after}"' if after else ''
        query = """
        query {
            shopifyPaymentsAccount {
                id
                disputes(first: """ + str(first) + after_part + """) {
                    edges {
                        node {
                            id
                            status
                            reasonDetails {
                                reason
                                networkReasonCode
                            }
                            amount {
                                amount
                                currencyCode
                            }
                            order {
                                id
                            }
                            initiatedAt
                            evidenceDueBy
                            evidenceSentOn
                            finalizedOn
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        }
        """
        
        return self.client.execute_graphql_query(query)
    
    def fetch_bank_accounts(self, first=50, after=None):
        """
        Fetch bank accounts from Shopify Payments account
        
        Args:
            first: Number of bank accounts to fetch
            after: Cursor for pagination
            
        Returns:
            dict: GraphQL response with bank accounts
        """
        after_part = f', after: "{after}"' if after else ''
        query = """
        query {
            shopifyPaymentsAccount {
                id
                bankAccounts(first: """ + str(first) + after_part + """) {
                    edges {
                        node {
                            id
                            bankName
                            currency
                            country
                            status
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        }
        """
        
        return self.client.execute_graphql_query(query)
    
    def fetch_account_info(self):
        """
        Fetch Shopify Payments account information
        
        Returns:
            dict: GraphQL response with account info
        """
        query = """
        query {
            shopifyPaymentsAccount {
                id
                activated
                country
                defaultCurrency
                onboardable
                payoutStatementDescriptor
                chargeStatementDescriptor
                balance {
                    amount
                    currencyCode
                }
            }
        }
        """
        
        return self.client.execute_graphql_query(query)
    
    def fetch_all_balance_transactions(self):
        """
        Fetch all balance transactions with pagination
        
        Returns:
            list: All balance transactions
        """
        all_transactions = []
        has_next_page = True
        after = None
        
        while has_next_page:
            response = self.fetch_balance_transactions(first=100, after=after)
            
            if 'data' in response and 'shopifyPaymentsAccount' in response['data']:
                account_data = response['data']['shopifyPaymentsAccount']
                if account_data and 'balanceTransactions' in account_data:
                    transactions_data = account_data['balanceTransactions']
                    
                    for edge in transactions_data.get('edges', []):
                        all_transactions.append(edge['node'])
                        after = edge.get('cursor')
                    
                    page_info = transactions_data.get('pageInfo', {})
                    has_next_page = page_info.get('hasNextPage', False)
                else:
                    has_next_page = False
            else:
                has_next_page = False
        
        return all_transactions
    
    def fetch_all_payouts(self):
        """
        Fetch all payouts with pagination
        
        Returns:
            list: All payouts
        """
        all_payouts = []
        has_next_page = True
        after = None
        
        while has_next_page:
            response = self.fetch_payouts(first=100, after=after)
            
            if 'data' in response and 'shopifyPaymentsAccount' in response['data']:
                account_data = response['data']['shopifyPaymentsAccount']
                if account_data and 'payouts' in account_data:
                    payouts_data = account_data['payouts']
                    
                    for edge in payouts_data.get('edges', []):
                        all_payouts.append(edge['node'])
                        after = edge.get('cursor')
                    
                    page_info = payouts_data.get('pageInfo', {})
                    has_next_page = page_info.get('hasNextPage', False)
                else:
                    has_next_page = False
            else:
                has_next_page = False
        
        return all_payouts
    
    def fetch_dispute_by_id(self, dispute_id):
        """
        Fetch a specific dispute by ID
        
        Args:
            dispute_id: Shopify dispute ID (e.g., "gid://shopify/ShopifyPaymentsDispute/598735659")
            
        Returns:
            dict: GraphQL response with dispute details
        """
        query = """
        query ShopifyPaymentsDisputesShow($id: ID!) {
            dispute(id: $id) {
                amount {
                    amount
                    currencyCode
                }
                evidenceDueBy
                evidenceSentOn
                finalizedOn
                id
                initiatedAt
                reasonDetails {
                    reason
                    networkReasonCode
                }
                status
                type
            }
        }
        """
        
        variables = {"id": dispute_id}
        return self.client.execute_graphql_query(query, variables)
    
    def fetch_dispute_evidence(self, evidence_id):
        """
        Fetch dispute evidence by ID
        
        Args:
            evidence_id: Shopify dispute evidence ID
            
        Returns:
            dict: GraphQL response with dispute evidence
        """
        query = """
        query ShopifyPaymentsDisputeEvidenceShow($id: ID!) {
            disputeEvidence(id: $id) {
                dispute {
                    amount {
                        amount
                        currencyCode
                    }
                    evidenceDueBy
                    evidenceSentOn
                    finalizedOn
                    id
                    initiatedAt
                    reasonDetails {
                        reason
                        networkReasonCode
                    }
                    status
                    type
                }
            }
        }
        """
        
        variables = {"id": evidence_id}
        return self.client.execute_graphql_query(query, variables)
    
    def fetch_finance_kyc_info(self):
        """
        Fetch KYC information for the shop's Shopify Payments account
        
        Returns:
            dict: GraphQL response with KYC information
        """
        # Note: financeKycInformation field is not available in current API
        # Return empty response for now
        return {"data": {}}
    
    def fetch_all_disputes(self, query_filter=None):
        """
        Fetch all disputes with optional filtering
        
        Args:
            query_filter: Optional query string for filtering (e.g., "status:NEEDS_RESPONSE")
            
        Returns:
            list: All disputes
        """
        all_disputes = []
        has_next_page = True
        after = None
        
        while has_next_page:
            # Build query with optional filter
            filter_param = f', query: "{query_filter}"' if query_filter else ''
            
            after_part = f', after: "{after}"' if after else ''
            query = """
            query {
                disputes(first: 100""" + after_part + filter_param + """) {
                    edges {
                        node {
                            id
                            status
                            type
                            reasonDetails {
                                reason
                                networkReasonCode
                            }
                            amount {
                                amount
                                currencyCode
                            }
                            initiatedAt
                            evidenceDueBy
                            evidenceSentOn
                            finalizedOn
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        """
        
        response = self.client.execute_graphql_query(query)
        
        if 'data' in response and 'disputes' in response['data']:
            disputes_data = response['data']['disputes']
            
            for edge in disputes_data.get('edges', []):
                all_disputes.append(edge['node'])
                after = edge.get('cursor')
            
            page_info = disputes_data.get('pageInfo', {})
            has_next_page = page_info.get('hasNextPage', False)
        else:
            has_next_page = False
        
        return all_disputes