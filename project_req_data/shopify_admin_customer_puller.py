#!/usr/bin/env python3
"""
Shopify Admin API Customer Puller
Converts Ruby GraphQL query to Python to retrieve all customers from Shopify store.
Uses the provided Admin API credentials for 7fa66c-ac.myshopify.com
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class ShopifyAdminCustomerPuller:
    def __init__(self, shop_domain: str, access_token: str, api_version: str = "2025-01"):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{shop_domain}/admin/api/{api_version}"
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Admin API requests"""
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def create_customer_graphql_query(self) -> str:
        """Create the GraphQL query to fetch all customers (basic fields first)"""
        query = """
        query CustomerList {
            customers(first: 50) {
                nodes {
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
                    addresses {
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
                    }
                    defaultAddress {
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
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        return query.strip()
    
    def execute_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query against Shopify Admin API"""
        url = f"{self.base_url}/graphql.json"
        
        payload = {
            "query": query
        }
        
        if variables:
            payload["variables"] = variables
            
        try:
            response = requests.post(
                url,
                headers=self.get_headers(),
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ GraphQL request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise
    
    def fetch_all_customers(self) -> List[Dict]:
        """Fetch all customers using pagination"""
        all_customers = []
        has_next_page = True
        cursor = None
        page_count = 0
        
        print("🔍 Starting customer data retrieval...")
        
        while has_next_page:
            page_count += 1
            print(f"📄 Fetching page {page_count}...")
            
            # Create query with pagination
            if cursor:
                query = self.create_paginated_query(cursor)
            else:
                query = self.create_customer_graphql_query()
            
            try:
                response = self.execute_graphql_query(query)
                
                if "errors" in response:
                    print(f"❌ GraphQL errors: {response['errors']}")
                    break
                
                customers_data = response.get("data", {}).get("customers", {})
                customers = customers_data.get("nodes", [])
                page_info = customers_data.get("pageInfo", {})
                
                all_customers.extend(customers)
                print(f"✅ Retrieved {len(customers)} customers from page {page_count}")
                
                # Check if there are more pages
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
                if not has_next_page:
                    print("📋 Reached end of customer data")
                    
            except Exception as e:
                print(f"❌ Error fetching page {page_count}: {e}")
                break
        
        print(f"🎯 Total customers retrieved: {len(all_customers)}")
        return all_customers
    
    def create_paginated_query(self, cursor: str) -> str:
        """Create GraphQL query with pagination cursor"""
        query = f"""
        query CustomerList {{
            customers(first: 50, after: "{cursor}") {{
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
    
    def analyze_customers(self, customers: List[Dict]) -> Dict:
        """Analyze customer data and generate insights"""
        if not customers:
            return {"error": "No customer data to analyze"}
        
        analysis = {
            "total_customers": len(customers),
            "customers_with_orders": 0,
            "total_amount_spent": 0.0,
            "currency": "AUD",  # Default for this store
            "verified_emails": 0,
            "customers_with_phone": 0,
            "customers_with_addresses": 0,
            "top_tags": {},
            "customer_states": {},
            "creation_dates": []
        }
        
        for customer in customers:
            # Count customers with orders
            num_orders = customer.get("numberOfOrders", 0)
            try:
                if int(num_orders) > 0:
                    analysis["customers_with_orders"] += 1
            except (ValueError, TypeError):
                pass
            
            # Note: totalSpent field not available in this API version
            # Will need to calculate from orders if needed
            
            # Count verified emails
            if customer.get("verifiedEmail"):
                analysis["verified_emails"] += 1
            
            # Count customers with phone numbers
            if customer.get("phone"):
                analysis["customers_with_phone"] += 1
            
            # Count customers with addresses
            if customer.get("addresses") and len(customer["addresses"]) > 0:
                analysis["customers_with_addresses"] += 1
            
            # Analyze tags
            tags = customer.get("tags", [])
            for tag in tags:
                analysis["top_tags"][tag] = analysis["top_tags"].get(tag, 0) + 1
            
            # Analyze customer states
            state = customer.get("state", "unknown")
            analysis["customer_states"][state] = analysis["customer_states"].get(state, 0) + 1
            
            # Collect creation dates
            created_at = customer.get("createdAt")
            if created_at:
                analysis["creation_dates"].append(created_at)
        
        # Sort tags by frequency
        analysis["top_tags"] = dict(sorted(analysis["top_tags"].items(), key=lambda x: x[1], reverse=True))
        
        return analysis
    
    def save_results(self, customers: List[Dict], analysis: Dict, filename_prefix: str = "shopify_customers") -> str:
        """Save customer data and analysis to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{self.shop_domain.replace('.', '_')}_{timestamp}.json"
        
        results = {
            "store_domain": self.shop_domain,
            "timestamp": timestamp,
            "api_version": self.api_version,
            "analysis": analysis,
            "customers": customers
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")
        return filename
    
    def print_summary(self, analysis: Dict):
        """Print a summary of the customer analysis"""
        print("\n" + "="*60)
        print("📊 CUSTOMER ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"🏪 Store: {self.shop_domain}")
        print(f"👥 Total Customers: {analysis['total_customers']}")
        print(f"🛒 Customers with Orders: {analysis['customers_with_orders']}")
        print(f"💰 Total Amount Spent: {analysis['total_amount_spent']:.2f} {analysis['currency']}")
        print(f"✅ Verified Emails: {analysis['verified_emails']}")
        print(f"📱 Customers with Phone: {analysis['customers_with_phone']}")
        print(f"🏠 Customers with Addresses: {analysis['customers_with_addresses']}")
        
        if analysis['top_tags']:
            print(f"\n🏷️  Top Customer Tags:")
            for tag, count in list(analysis['top_tags'].items())[:5]:
                print(f"   {tag}: {count}")
        
        if analysis['customer_states']:
            print(f"\n📈 Customer States:")
            for state, count in analysis['customer_states'].items():
                print(f"   {state}: {count}")

def main():
    # Shopify store credentials (load from environment variables)
    SHOP_DOMAIN = os.getenv('SHOPIFY_STORE_DOMAIN', 'your-store.myshopify.com')
    ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', 'your_access_token_here')
    API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2025-01')
    
    print("🛍️  Shopify Admin API Customer Puller")
    print(f"Store: {SHOP_DOMAIN}")
    print("="*60)
    
    # Initialize the customer puller
    puller = ShopifyAdminCustomerPuller(SHOP_DOMAIN, ACCESS_TOKEN, API_VERSION)
    
    try:
        # Fetch all customers
        customers = puller.fetch_all_customers()
        
        if customers:
            # Analyze customer data
            analysis = puller.analyze_customers(customers)
            
            # Print summary
            puller.print_summary(analysis)
            
            # Save results
            filename = puller.save_results(customers, analysis)
            
            print(f"\n✅ SUCCESS: Retrieved and analyzed {len(customers)} customers")
            print(f"📄 Data saved to: {filename}")
            
        else:
            print("❌ No customers found or error occurred")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()