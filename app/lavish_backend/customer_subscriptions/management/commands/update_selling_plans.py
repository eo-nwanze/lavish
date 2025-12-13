"""
Django Management Command: Update Existing Selling Plans in Shopify

This updates the discount percentages in EXISTING Shopify selling plan groups
instead of creating new ones.
"""

from django.core.management.base import BaseCommand
from customer_subscriptions.models import SellingPlan
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update existing selling plans in Shopify with correct discount percentages'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("UPDATE EXISTING SELLING PLANS IN SHOPIFY"))
        self.stdout.write("="*80 + "\n")
        
        client = EnhancedShopifyAPIClient()
        plans = SellingPlan.objects.filter(shopify_selling_plan_group_id__isnull=False).order_by('id')
        
        self.stdout.write(f"Found {plans.count()} selling plans with Shopify groups\n")
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for plan in plans:
            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write(f"Updating: {plan.name}")
            self.stdout.write(f"   Group ID: {plan.shopify_selling_plan_group_id}")
            self.stdout.write(f"   Plan ID: {plan.shopify_id}")
            self.stdout.write(f"   Django has: {plan.price_adjustment_value}% discount")
            
            # Build pricing policy
            pricing_policies = [{
                "fixed": {
                    "adjustmentType": "PERCENTAGE",
                    "adjustmentValue": {
                        "percentage": float(plan.price_adjustment_value)
                    }
                }
            }]
            
            # Update selling plan mutation
            mutation = """
            mutation sellingPlanUpdate($id: ID!, $input: SellingPlanInput!) {
              sellingPlanUpdate(id: $id, input: $input) {
                sellingPlan {
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
                userErrors {
                  field
                  message
                }
              }
            }
            """
            
            variables = {
                "id": plan.shopify_id,
                "input": {
                    "name": plan.name,
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
                }
            }
            
            try:
                result = client.execute_graphql_query(mutation, variables)
                
                if result:
                    data = result.get("data", {}).get("sellingPlanUpdate", {})
                    user_errors = data.get("userErrors", [])
                    
                    if user_errors:
                        results["failed"] += 1
                        error_msg = "; ".join([e.get("message", "Unknown") for e in user_errors])
                        results["errors"].append(f"{plan.name}: {error_msg}")
                        self.stdout.write(self.style.ERROR(f"   FAILED: {error_msg}"))
                    else:
                        results["success"] += 1
                        selling_plan_data = data.get("sellingPlan", {})
                        
                        # Get the updated percentage
                        pricing_policies_result = selling_plan_data.get("pricingPolicies", [])
                        if pricing_policies_result:
                            adj_value = pricing_policies_result[0].get("adjustmentValue", {})
                            percentage = adj_value.get("percentage", "Unknown")
                            self.stdout.write(self.style.SUCCESS(f"   SUCCESS: Updated to {percentage}% discount"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"   SUCCESS: Selling plan updated"))
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{plan.name}: No response from Shopify")
                    self.stdout.write(self.style.ERROR(f"   FAILED: No response from Shopify"))
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = str(e)
                results["errors"].append(f"{plan.name}: {error_msg}")
                self.stdout.write(self.style.ERROR(f"   EXCEPTION: {error_msg}"))
        
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
            self.stdout.write(self.style.SUCCESS("ALL PLANS UPDATED SUCCESSFULLY!"))
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Refresh your Shopify product page (Ctrl+Shift+R)")
            self.stdout.write("2. Check browser console for updated percentages")
            self.stdout.write("3. Verify discounts show correctly on frontend")
        elif results["success"] > 0:
            self.stdout.write(self.style.WARNING("PARTIAL SUCCESS"))
            self.stdout.write(f"\n{results['success']} plans updated, but {results['failed']} failed.")
        else:
            self.stdout.write(self.style.ERROR("ALL UPDATES FAILED"))
        
        self.stdout.write("="*80 + "\n")

