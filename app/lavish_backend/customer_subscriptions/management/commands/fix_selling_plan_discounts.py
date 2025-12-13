"""
Fix Selling Plan Discounts - Update Selling Plan Groups in Shopify

Since individual selling plans can't be updated, we need to update the entire
selling plan GROUP with the correct pricing policies.
"""

from django.core.management.base import BaseCommand
from customer_subscriptions.models import SellingPlan
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update selling plan groups in Shopify with correct discount percentages'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("FIX SELLING PLAN GROUP DISCOUNTS"))
        self.stdout.write("="*80 + "\n")
        
        client = EnhancedShopifyAPIClient()
        plans = SellingPlan.objects.filter(shopify_selling_plan_group_id__isnull=False).order_by('id')
        
        self.stdout.write(f"Found {plans.count()} selling plans\n")
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for plan in plans:
            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write(f"Updating GROUP for: {plan.name}")
            self.stdout.write(f"   Group ID: {plan.shopify_selling_plan_group_id}")
            self.stdout.write(f"   Selling Plan ID: {plan.shopify_id}")
            self.stdout.write(f"   Django discount: {plan.price_adjustment_value}%")
            
            # Update the GROUP mutation
            mutation = """
            mutation sellingPlanGroupUpdate($id: ID!, $input: SellingPlanGroupInput!) {
              sellingPlanGroupUpdate(id: $id, input: $input) {
                sellingPlanGroup {
                  id
                  name
                  sellingPlans(first: 10) {
                    edges {
                      node {
                        id
                        name
                        pricingPolicies {
                          ... on SellingPlanFixedPricingPolicy {
                            adjustmentType
                            adjustmentValue {
                              ... on SellingPlanPricingPolicyPercentageValue {
                                percentage
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
            
            # Build pricing policies
            pricing_policies = [{
                "fixed": {
                    "adjustmentType": "PERCENTAGE",
                    "adjustmentValue": {
                        "percentage": float(plan.price_adjustment_value)
                    }
                }
            }]
            
            # Update the group with the selling plan configuration
            variables = {
                "id": plan.shopify_selling_plan_group_id,
                "input": {
                    "name": plan.name or f"Subscription Plan {plan.id}",
                    "description": plan.description,
                    "options": ["Subscription"],
                    "sellingPlansToUpdate": [{
                        "id": plan.shopify_id,
                        "name": plan.name,
                        "options": ["Subscription"],
                        "billingPolicy": {
                            "recurring": {
                                "interval": plan.billing_interval,
                                "intervalCount": plan.billing_interval_count
                            }
                        },
                        "deliveryPolicy": {
                            "recurring": {
                                "interval": plan.delivery_interval,
                                "intervalCount": plan.delivery_interval_count
                            }
                        },
                        "pricingPolicies": pricing_policies
                    }]
                }
            }
            
            try:
                result = client.execute_graphql_query(mutation, variables)
                
                if result:
                    data = result.get("data", {}).get("sellingPlanGroupUpdate", {})
                    user_errors = data.get("userErrors", [])
                    
                    if user_errors:
                        results["failed"] += 1
                        error_msg = "; ".join([e.get("message", "Unknown") for e in user_errors])
                        results["errors"].append(f"{plan.name}: {error_msg}")
                        self.stdout.write(self.style.ERROR(f"   FAILED: {error_msg}"))
                    else:
                        results["success"] += 1
                        group_data = data.get("sellingPlanGroup", {})
                        selling_plans = group_data.get("sellingPlans", {}).get("edges", [])
                        
                        if selling_plans:
                            updated_plan = selling_plans[0].get("node", {})
                            pricing_policies_result = updated_plan.get("pricingPolicies", [])
                            if pricing_policies_result:
                                adj_value = pricing_policies_result[0].get("adjustmentValue", {})
                                percentage = adj_value.get("percentage", "Unknown")
                                self.stdout.write(self.style.SUCCESS(f"   SUCCESS: Shopify now has {percentage}% discount"))
                            else:
                                self.stdout.write(self.style.SUCCESS(f"   SUCCESS: Group updated"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"   SUCCESS: Group updated"))
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{plan.name}: No response from Shopify")
                    self.stdout.write(self.style.ERROR(f"   FAILED: No response from Shopify"))
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = str(e)
                results["errors"].append(f"{plan.name}: {error_msg}")
                self.stdout.write(self.style.ERROR(f"   EXCEPTION: {error_msg}"))
                logger.exception(f"Error updating {plan.name}")
        
        # Summary
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS("UPDATE SUMMARY"))
        self.stdout.write("="*80)
        self.stdout.write(f"Successful: {results['success']}/{plans.count()}")
        self.stdout.write(f"Failed: {results['failed']}/{plans.count()}")
        
        if results["errors"]:
            self.stdout.write(self.style.WARNING(f"\nERRORS:"))
            for error in results["errors"]:
                self.stdout.write(f"   - {error}")
        
        self.stdout.write("\n" + "="*80)
        
        if results["success"] == plans.count():
            self.stdout.write(self.style.SUCCESS("ALL PLANS UPDATED!"))
            self.stdout.write("\nIMPORTANT NEXT STEPS:")
            self.stdout.write("1. Hard refresh browser (Ctrl+Shift+R)")
            self.stdout.write("2. Check console for [Lavish Frontend] messages")
            self.stdout.write("3. Should now show correct percentages!")
        elif results["success"] > 0:
            self.stdout.write(self.style.WARNING("PARTIAL SUCCESS"))
        else:
            self.stdout.write(self.style.ERROR("ALL UPDATES FAILED"))
        
        self.stdout.write("="*80 + "\n")

