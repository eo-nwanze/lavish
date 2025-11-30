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
                "pricingPolicies": [{
                    "fixed": {
                        "adjustmentType": selling_plan.price_adjustment_type,
                        "adjustmentValue": {
                            "percentage" if selling_plan.price_adjustment_type == "PERCENTAGE" else "fixedValue": float(selling_plan.price_adjustment_value)
                        }
                    }
                }]
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
    
    # ==================== SUBSCRIPTION CONTRACT SYNC ====================
    
    def create_subscription_in_shopify(self, subscription) -> Dict:
        """
        Create a subscription contract in Shopify
        
        Args:
            subscription: CustomerSubscription instance
            
        Returns:
            Dict with success status and details
        """
        mutation = """
        mutation subscriptionDraftCreate($input: SubscriptionDraftInput!) {
          subscriptionDraftCreate(input: $input) {
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
        
        # Build subscription draft input
        draft_input = {
            "customerId": subscription.customer.shopify_id,
            "nextBillingDate": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            "billingPolicy": {
                "interval": subscription.billing_policy_interval,
                "intervalCount": subscription.billing_policy_interval_count
            },
            "deliveryPolicy": {
                "interval": subscription.delivery_policy_interval,
                "intervalCount": subscription.delivery_policy_interval_count
            },
            "status": subscription.status,
            "currencyCode": subscription.currency
        }
        
        # Add line items
        if subscription.line_items:
            draft_input["lines"] = []
            for item in subscription.line_items:
                line = {
                    "productVariantId": item.get("variant_id"),
                    "quantity": item.get("quantity", 1)
                }
                if "selling_plan_id" in item:
                    line["sellingPlanId"] = item["selling_plan_id"]
                draft_input["lines"].append(line)
        
        # Add delivery address
        if subscription.delivery_address:
            draft_input["deliveryMethod"] = {
                "shipping": {
                    "address": subscription.delivery_address
                }
            }
        
        variables = {"input": draft_input}
        
        try:
            # Step 1: Create draft
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result or result.get("data", {}).get("subscriptionDraftCreate", {}).get("userErrors"):
                errors = result.get("errors") or result["data"]["subscriptionDraftCreate"]["userErrors"]
                logger.error(f"Subscription draft creation failed: {errors}")
                return {
                    "success": False,
                    "errors": errors,
                    "message": "Failed to create subscription draft"
                }
            
            draft_id = result["data"]["subscriptionDraftCreate"]["draft"]["id"]
            
            # Step 2: Commit draft to create active subscription
            commit_result = self._commit_subscription_draft(draft_id)
            
            if commit_result.get("success"):
                contract_id = commit_result.get("contract_id")
                
                with transaction.atomic():
                    subscription.shopify_id = contract_id
                    subscription.needs_shopify_push = False
                    subscription.shopify_push_error = ""
                    subscription.last_pushed_to_shopify = timezone.now()
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
        
        mutation = """
        mutation subscriptionContractUpdate($contractId: ID!, $input: SubscriptionContractUpdateInput!) {
          subscriptionContractUpdate(contractId: $contractId, input: $input) {
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
        
        update_input = {}
        
        if subscription.next_billing_date:
            update_input["nextBillingDate"] = subscription.next_billing_date.isoformat()
        
        variables = {
            "contractId": subscription.shopify_id,
            "input": update_input
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result or result.get("data", {}).get("subscriptionContractUpdate", {}).get("userErrors"):
                errors = result.get("errors") or result["data"]["subscriptionContractUpdate"]["userErrors"]
                logger.error(f"Subscription update failed: {errors}")
                return {
                    "success": False,
                    "errors": errors,
                    "message": "Failed to update subscription"
                }
            
            with transaction.atomic():
                subscription.needs_shopify_push = False
                subscription.shopify_push_error = ""
                subscription.last_pushed_to_shopify = timezone.now()
                subscription.save()
            
            logger.info(f"Successfully updated subscription in Shopify: {subscription.shopify_id}")
            return {
                "success": True,
                "message": "Subscription updated in Shopify"
            }
            
        except Exception as e:
            logger.error(f"Exception updating subscription: {e}")
            subscription.shopify_push_error = str(e)
            subscription.save()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update subscription: {e}"
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
