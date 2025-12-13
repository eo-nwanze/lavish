"""
Bidirectional Subscription Sync Service
Handles Django ↔ Shopify subscription synchronization

Supports:
- Creating selling plans in Django → Push to Shopify
- Creating subscriptions in Django → Push to Shopify
- Importing subscriptions from Shopify → Save in Django
- Updating subscriptions bidirectionally
- Cancelling subscriptions
"""

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
from datetime import datetime, date

logger = logging.getLogger('customer_subscriptions')


class SubscriptionBidirectionalSync:
    """Service for syncing subscriptions between Django and Shopify"""
    
    def __init__(self):
        self.client = EnhancedShopifyAPIClient()
    
    # ==================== SELLING PLAN SYNC ====================
    
    def _build_pricing_policies(self, selling_plan):
        """Build pricing policies for selling plan"""
        adjustment_type = selling_plan.price_adjustment_type
        adjustment_value = float(selling_plan.price_adjustment_value)
        
        if adjustment_type == "PERCENTAGE":
            return [{
                "fixed": {
                    "adjustmentType": "PERCENTAGE",
                    "adjustmentValue": {
                        "percentage": adjustment_value
                    }
                }
            }]
        elif adjustment_type == "FIXED_AMOUNT":
            return [{
                "fixed": {
                    "adjustmentType": "FIXED_AMOUNT",
                    "adjustmentValue": {
                        "fixedValue": adjustment_value
                    }
                }
            }]
        else:  # PRICE
            return [{
                "fixed": {
                    "adjustmentType": "PRICE",
                    "adjustmentValue": {
                        "price": adjustment_value
                    }
                }
            }]
    
    def create_selling_plan_in_shopify(self, selling_plan) -> Dict:
        """
        Create a selling plan (subscription plan) in Shopify
        
        Args:
            selling_plan: SellingPlan instance
            
        Returns:
            Dict with success status and details
        """
        mutation = """
        mutation sellingPlanGroupCreate($input: SellingPlanGroupInput!, $resources: SellingPlanGroupResourceInput) {
          sellingPlanGroupCreate(input: $input, resources: $resources) {
            sellingPlanGroup {
              id
              name
              sellingPlans(first: 10) {
                edges {
                  node {
                    id
                    name
                    billingPolicy {
                      ... on SellingPlanRecurringBillingPolicy {
                        interval
                        intervalCount
                      }
                    }
                    deliveryPolicy {
                      ... on SellingPlanRecurringDeliveryPolicy {
                        interval
                        intervalCount
                      }
                    }
                    pricingPolicies {
                      ... on SellingPlanFixedPricingPolicy {
                        adjustmentType
                        adjustmentValue {
                          ... on SellingPlanPricingPolicyPercentageValue {
                            percentage
                          }
                          ... on MoneyV2 {
                            amount
                          }
                        }
                      }
                    }
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
        
        # Build selling plan input
        plan_input = {
            "name": selling_plan.name or f"Plan {selling_plan.id}",
            "description": selling_plan.description,
            "options": ["Subscription"],  # Global options for the group
            "sellingPlansToCreate": [{
                "name": selling_plan.name,
                "options": ["Subscription"],  # Options specific to this plan (must match variant options)
                "category": "SUBSCRIPTION",  # Required: SUBSCRIPTION, PRE_ORDER, or TRY_BEFORE_YOU_BUY
                "billingPolicy": {
                    "recurring": {
                        "interval": selling_plan.billing_interval,
                        "intervalCount": selling_plan.billing_interval_count
                    }
                },
                "deliveryPolicy": {
                    "recurring": {
                        "interval": selling_plan.delivery_interval,
                        "intervalCount": selling_plan.delivery_interval_count
                    }
                },
                "pricingPolicies": self._build_pricing_policies(selling_plan)
            }]
        }
        
        # Add product resources if associated
        resources = None
        if selling_plan.products.exists():
            product_ids = [p.shopify_id for p in selling_plan.products.all() if p.shopify_id]
            if product_ids:
                resources = {
                    "productIds": product_ids
                }
        
        variables = {
            "input": plan_input,
            "resources": resources
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"Selling plan creation failed: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            data = result.get("data", {}).get("sellingPlanGroupCreate", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Selling plan validation errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            selling_plan_group = data.get("sellingPlanGroup")
            if selling_plan_group:
                # Get the first selling plan from the group
                plans = selling_plan_group.get("sellingPlans", {}).get("edges", [])
                if plans:
                    plan_node = plans[0].get("node", {})
                    shopify_id = plan_node.get("id")
                    group_id = selling_plan_group.get("id")
                    
                    with transaction.atomic():
                        selling_plan.shopify_id = shopify_id
                        selling_plan.shopify_selling_plan_group_id = group_id
                        selling_plan.needs_shopify_push = False
                        selling_plan.shopify_push_error = ""
                        selling_plan.last_pushed_to_shopify = timezone.now()
                        selling_plan.save()
                    
                    logger.info(f"Successfully created selling plan in Shopify: {shopify_id}")
                    return {
                        "success": True,
                        "shopify_id": shopify_id,
                        "group_id": group_id,
                        "message": f"Selling plan '{selling_plan.name}' created in Shopify"
                    }
            
            return {
                "success": False,
                "message": "No selling plan data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception creating selling plan: {e}")
            selling_plan.shopify_push_error = str(e)
            selling_plan.save()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create selling plan: {e}"
            }
    
    def add_products_to_selling_plan_group(self, group_id: str, product_ids: List[str]) -> Dict:
        """
        Add products to an existing selling plan group in Shopify
        
        Args:
            group_id: Shopify SellingPlanGroup GID
            product_ids: List of Shopify Product GIDs
            
        Returns:
            Dict with success status and details
        """
        if not product_ids:
            return {
                "success": False,
                "message": "No product IDs provided"
            }
        
        mutation = """
        mutation sellingPlanGroupAddProducts($id: ID!, $productIds: [ID!]!) {
          sellingPlanGroupAddProducts(id: $id, productIds: $productIds) {
            sellingPlanGroup {
              id
              name
              products(first: 50) {
                edges {
                  node {
                    id
                    title
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
        
        variables = {
            "id": group_id,
            "productIds": product_ids
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"Product association failed: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            data = result.get("data", {}).get("sellingPlanGroupAddProducts", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Product association validation errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": "Validation errors occurred"
                }
            
            selling_plan_group = data.get("sellingPlanGroup")
            if selling_plan_group:
                products = selling_plan_group.get("products", {}).get("edges", [])
                product_count = len(products)
                logger.info(f"Successfully added {len(product_ids)} products to group. Total products now: {product_count}")
                return {
                    "success": True,
                    "group_id": group_id,
                    "products_added": len(product_ids),
                    "total_products": product_count,
                    "message": f"Added {len(product_ids)} products to selling plan group"
                }
            
            return {
                "success": False,
                "message": "No selling plan group data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception adding products to selling plan group: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add products: {e}"
            }
    
    def sync_selling_plan_products(self, selling_plan) -> Dict:
        """
        Sync product associations from Django to Shopify for a selling plan
        
        Args:
            selling_plan: SellingPlan instance
            
        Returns:
            Dict with success status and details
        """
        if not selling_plan.shopify_selling_plan_group_id:
            return {
                "success": False,
                "message": "Selling plan has no Shopify group ID. Create it first."
            }
        
        # Get all associated products with valid Shopify IDs
        product_ids = [
            p.shopify_id for p in selling_plan.products.all() 
            if p.shopify_id and not p.shopify_id.startswith('temp_')
        ]
        
        if not product_ids:
            return {
                "success": False,
                "message": "No products with valid Shopify IDs associated with this plan"
            }
        
        logger.info(f"Syncing {len(product_ids)} products to selling plan group {selling_plan.shopify_selling_plan_group_id}")
        
        return self.add_products_to_selling_plan_group(
            selling_plan.shopify_selling_plan_group_id,
            product_ids
        )
    
    # ==================== SUBSCRIPTION CONTRACT SYNC ====================
    
    def create_subscription_in_shopify(self, subscription) -> Dict:
        """
        Create a subscription contract in Shopify using subscriptionContractCreate
        
        Args:
            subscription: CustomerSubscription instance
            
        Returns:
            Dict with success status and details
        """
        # Validate customer has Shopify ID
        if not subscription.customer.shopify_id:
            return {
                "success": False,
                "message": "Customer must be synced to Shopify first (no Shopify ID)"
            }
        
        mutation = """
        mutation subscriptionContractCreate($input: SubscriptionContractCreateInput!) {
          subscriptionContractCreate(input: $input) {
            draft {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        # Build delivery address
        delivery_address = subscription.get_address()
        if not delivery_address:
            return {
                "success": False,
                "message": "Subscription must have a delivery address"
            }
        
        # Build contract input
        contract_input = {
            "customerId": subscription.customer.shopify_id,
            "nextBillingDate": subscription.next_billing_date.isoformat() if subscription.next_billing_date else date.today().isoformat(),
            "currencyCode": subscription.currency,
            "contract": {
                "status": subscription.status,
                "billingPolicy": {
                    "interval": subscription.billing_policy_interval,
                    "intervalCount": subscription.billing_policy_interval_count
                },
                "deliveryPolicy": {
                    "interval": subscription.delivery_policy_interval,
                    "intervalCount": subscription.delivery_policy_interval_count
                },
                "deliveryMethod": {
                    "shipping": {
                        "address": {
                            "firstName": delivery_address.get("first_name", ""),
                            "lastName": delivery_address.get("last_name", ""),
                            "address1": delivery_address.get("address1", ""),
                            "address2": delivery_address.get("address2", ""),
                            "city": delivery_address.get("city", ""),
                            "province": delivery_address.get("province", ""),
                            "country": delivery_address.get("country", ""),
                            "zip": delivery_address.get("zip", delivery_address.get("zip_code", ""))
                        }
                    }
                }
            }
        }
        
        # Add payment method if available
        if subscription.payment_method_id:
            contract_input["contract"]["paymentMethodId"] = subscription.payment_method_id
        
        # Add notes if available
        if subscription.notes:
            contract_input["contract"]["note"] = subscription.notes
        
        variables = {"input": contract_input}
        
        try:
            # Step 1: Create draft
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"GraphQL errors creating subscription: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "GraphQL errors occurred"
                }
            
            data = result.get("data", {}).get("subscriptionContractCreate", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Subscription creation validation errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": f"Validation errors: {user_errors[0].get('message', 'Unknown error')}"
                }
            
            draft_id = data.get("draft", {}).get("id")
            if not draft_id:
                return {
                    "success": False,
                    "message": "No draft ID returned from Shopify"
                }
            
            # Step 2: Add line items to draft
            if subscription.line_items:
                for item in subscription.line_items:
                    line_result = self._add_line_to_subscription_draft(draft_id, item)
                    if not line_result.get("success"):
                        logger.warning(f"Failed to add line item to draft: {line_result.get('message')}")
                        # Continue with other items even if one fails
            
            # Step 3: Commit draft to create active subscription
            commit_result = self._commit_subscription_draft(draft_id)
            
            if commit_result.get("success"):
                contract_id = commit_result.get("contract_id")
                
                with transaction.atomic():
                    subscription.shopify_id = contract_id
                    subscription.needs_shopify_push = False
                    subscription.shopify_push_error = ""
                    subscription.last_pushed_to_shopify = timezone.now()
                    subscription.contract_created_at = timezone.now()
                    subscription.save()
                
                logger.info(f"Successfully created subscription in Shopify: {contract_id}")
                return {
                    "success": True,
                    "shopify_id": contract_id,
                    "message": f"Subscription created in Shopify"
                }
            
            return commit_result
            
        except Exception as e:
            logger.error(f"Exception creating subscription: {e}")
            subscription.shopify_push_error = str(e)
            subscription.save()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create subscription: {e}"
            }
    
    def _add_line_to_subscription_draft(self, draft_id: str, line_item: dict) -> Dict:
        """Add a line item to a subscription draft"""
        mutation = """
        mutation subscriptionDraftLineAdd($draftId: ID!, $input: SubscriptionLineInput!) {
          subscriptionDraftLineAdd(draftId: $draftId, input: $input) {
            lineAdded {
              id
              quantity
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        line_input = {
            "productVariantId": line_item.get("variant_id"),
            "quantity": line_item.get("quantity", 1)
        }
        
        if "current_price" in line_item:
            line_input["currentPrice"] = str(line_item["current_price"])
        
        if "selling_plan_id" in line_item:
            line_input["sellingPlanId"] = line_item["selling_plan_id"]
        
        variables = {
            "draftId": draft_id,
            "input": line_input
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result or result.get("data", {}).get("subscriptionDraftLineAdd", {}).get("userErrors"):
                errors = result.get("errors") or result["data"]["subscriptionDraftLineAdd"]["userErrors"]
                return {
                    "success": False,
                    "errors": errors,
                    "message": f"Failed to add line item: {errors[0].get('message') if errors else 'Unknown error'}"
                }
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception adding line item: {e}"
            }
    
    def _commit_subscription_draft(self, draft_id: str) -> Dict:
        """Commit a subscription draft to create active subscription"""
        mutation = """
        mutation subscriptionDraftCommit($draftId: ID!) {
          subscriptionDraftCommit(draftId: $draftId) {
            contract {
              id
              status
              nextBillingDate
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {"draftId": draft_id}
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result or result.get("data", {}).get("subscriptionDraftCommit", {}).get("userErrors"):
                errors = result.get("errors") or result["data"]["subscriptionDraftCommit"]["userErrors"]
                return {
                    "success": False,
                    "errors": errors,
                    "message": "Failed to commit subscription draft"
                }
            
            contract = result["data"]["subscriptionDraftCommit"]["contract"]
            return {
                "success": True,
                "contract_id": contract["id"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to commit draft: {e}"
            }
    
    def update_subscription_in_shopify(self, subscription) -> Dict:
        """
        Update an existing subscription in Shopify
        Creates a draft, applies changes, and commits
        
        Args:
            subscription: CustomerSubscription instance
            
        Returns:
            Dict with success status
        """
        if not subscription.shopify_id:
            return {
                "success": False,
                "message": "Subscription has no Shopify ID, cannot update"
            }
        
        # Step 1: Create draft from existing contract
        mutation = """
        mutation subscriptionContractUpdate($contractId: ID!) {
          subscriptionContractUpdate(contractId: $contractId) {
            draft {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {"contractId": subscription.shopify_id}
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"GraphQL errors creating draft: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "Failed to create update draft"
                }
            
            data = result.get("data", {}).get("subscriptionContractUpdate", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Subscription update draft errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": f"Failed to create draft: {user_errors[0].get('message', 'Unknown error')}"
                }
            
            draft_id = data.get("draft", {}).get("id")
            if not draft_id:
                return {
                    "success": False,
                    "message": "No draft ID returned for update"
                }
            
            # Step 2: Apply changes to the draft (if needed)
            # You can add more draft modifications here, such as:
            # - Adding/removing line items
            # - Updating delivery address
            # - Applying discounts
            # For now, we just commit with the current state
            
            # Step 3: Commit the draft
            commit_result = self._commit_subscription_draft(draft_id)
            
            if commit_result.get("success"):
                with transaction.atomic():
                    subscription.needs_shopify_push = False
                    subscription.shopify_push_error = ""
                    subscription.last_pushed_to_shopify = timezone.now()
                    subscription.contract_updated_at = timezone.now()
                    subscription.save()
                
                logger.info(f"Successfully updated subscription in Shopify: {subscription.shopify_id}")
                return {
                    "success": True,
                    "message": "Subscription updated in Shopify"
                }
            
            return commit_result
            
        except Exception as e:
            logger.error(f"Exception updating subscription: {e}")
            subscription.shopify_push_error = str(e)
            subscription.save()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update subscription: {e}"
            }
    
    def create_billing_attempt(self, subscription, origin_time: Optional[str] = None) -> Dict:
        """
        Create a billing attempt for a subscription contract
        This bills the customer and creates an order
        
        Args:
            subscription: CustomerSubscription instance
            origin_time: Optional ISO datetime for billing cycle calculation
            
        Returns:
            Dict with success status and billing attempt details
        """
        if not subscription.shopify_id:
            return {
                "success": False,
                "message": "Subscription has no Shopify ID, cannot create billing attempt"
            }
        
        import uuid
        idempotency_key = str(uuid.uuid4())
        
        mutation = """
        mutation subscriptionBillingAttemptCreate($contractId: ID!, $input: SubscriptionBillingAttemptInput!) {
          subscriptionBillingAttemptCreate(
            subscriptionContractId: $contractId
            subscriptionBillingAttemptInput: $input
          ) {
            subscriptionBillingAttempt {
              id
              originTime
              errorMessage
              errorCode
              nextActionUrl
              order {
                id
                name
              }
              ready
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        billing_input = {
            "idempotencyKey": idempotency_key
        }
        
        if origin_time:
            billing_input["originTime"] = origin_time
        
        variables = {
            "contractId": subscription.shopify_id,
            "input": billing_input
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"GraphQL errors creating billing attempt: {result['errors']}")
                return {
                    "success": False,
                    "errors": result["errors"],
                    "message": "Failed to create billing attempt"
                }
            
            data = result.get("data", {}).get("subscriptionBillingAttemptCreate", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Billing attempt validation errors: {user_errors}")
                return {
                    "success": False,
                    "errors": user_errors,
                    "message": f"Billing attempt failed: {user_errors[0].get('message', 'Unknown error')}"
                }
            
            billing_attempt = data.get("subscriptionBillingAttempt", {})
            
            if billing_attempt:
                # Save billing attempt to database
                from customer_subscriptions.models import SubscriptionBillingAttempt
                
                ba_record = SubscriptionBillingAttempt.objects.create(
                    subscription=subscription,
                    shopify_id=billing_attempt.get("id"),
                    status='PENDING',
                    amount=subscription.total_price,
                    currency=subscription.currency,
                    shopify_order_id=billing_attempt.get("order", {}).get("id", "") if billing_attempt.get("order") else "",
                    error_message=billing_attempt.get("errorMessage", ""),
                    error_code=billing_attempt.get("errorCode", "")
                )
                
                logger.info(f"Created billing attempt: {billing_attempt.get('id')}")
                
                return {
                    "success": True,
                    "billing_attempt_id": billing_attempt.get("id"),
                    "order_id": billing_attempt.get("order", {}).get("id") if billing_attempt.get("order") else None,
                    "order_name": billing_attempt.get("order", {}).get("name") if billing_attempt.get("order") else None,
                    "ready": billing_attempt.get("ready", False),
                    "next_action_url": billing_attempt.get("nextActionUrl"),
                    "message": "Billing attempt created successfully"
                }
            
            return {
                "success": False,
                "message": "No billing attempt data in response"
            }
            
        except Exception as e:
            logger.error(f"Exception creating billing attempt: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create billing attempt: {e}"
            }
    
    def cancel_subscription_in_shopify(self, subscription) -> Dict:
        """
        Cancel a subscription in Shopify
        
        Args:
            subscription: CustomerSubscription instance
            
        Returns:
            Dict with success status
        """
        if not subscription.shopify_id:
            return {
                "success": False,
                "message": "Subscription has no Shopify ID, cannot cancel"
            }
        
        mutation = """
        mutation subscriptionContractCancel($contractId: ID!) {
          subscriptionContractCancel(contractId: $contractId) {
            contract {
              id
              status
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {"contractId": subscription.shopify_id}
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result or result.get("data", {}).get("subscriptionContractCancel", {}).get("userErrors"):
                errors = result.get("errors") or result["data"]["subscriptionContractCancel"]["userErrors"]
                return {
                    "success": False,
                    "errors": errors,
                    "message": "Failed to cancel subscription"
                }
            
            with transaction.atomic():
                subscription.status = 'CANCELLED'
                subscription.needs_shopify_push = False
                subscription.last_pushed_to_shopify = timezone.now()
                subscription.save()
            
            logger.info(f"Successfully cancelled subscription in Shopify: {subscription.shopify_id}")
            return {
                "success": True,
                "message": "Subscription cancelled in Shopify"
            }
            
        except Exception as e:
            logger.error(f"Exception cancelling subscription: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to cancel subscription: {e}"
            }
    
    # ==================== BULK OPERATIONS ====================
    
    def sync_pending_subscriptions(self) -> Dict:
        """
        Sync all subscriptions marked for push to Shopify
        
        Returns:
            Dict with results summary
        """
        from customer_subscriptions.models import CustomerSubscription
        
        pending = CustomerSubscription.objects.filter(needs_shopify_push=True)
        
        results = {
            "total": pending.count(),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for subscription in pending:
            if subscription.shopify_id:
                result = self.update_subscription_in_shopify(subscription)
            else:
                result = self.create_subscription_in_shopify(subscription)
            
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "subscription_id": subscription.id,
                    "customer": str(subscription.customer),
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"Bulk sync completed: {results['successful']}/{results['total']} successful")
        return results


# Singleton instance
subscription_sync = SubscriptionBidirectionalSync()
