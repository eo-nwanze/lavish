from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import (
    SellingPlan, CustomerSubscription, SubscriptionBillingAttempt, 
    SubscriptionSyncLog, SubscriptionAddress, OrderAddressOverride,
    ProductShippingConfig, ShippingCutoffLog
)
from .bidirectional_sync import subscription_sync


# Import-Export Resources
class SellingPlanResource(resources.ModelResource):
    class Meta:
        model = SellingPlan
        import_id_fields = ['shopify_id']


class CustomerSubscriptionResource(resources.ModelResource):
    class Meta:
        model = CustomerSubscription
        import_id_fields = ['shopify_id']


class SubscriptionBillingAttemptResource(resources.ModelResource):
    class Meta:
        model = SubscriptionBillingAttempt
        import_id_fields = ['shopify_id']


class SubscriptionSyncLogResource(resources.ModelResource):
    class Meta:
        model = SubscriptionSyncLog
        import_id_fields = ['id']


class SubscriptionAddressResource(resources.ModelResource):
    class Meta:
        model = SubscriptionAddress
        import_id_fields = ['id']


class OrderAddressOverrideResource(resources.ModelResource):
    class Meta:
        model = OrderAddressOverride
        import_id_fields = ['id']


class ProductShippingConfigResource(resources.ModelResource):
    class Meta:
        model = ProductShippingConfig
        import_id_fields = ['id']


class ShippingCutoffLogResource(resources.ModelResource):
    class Meta:
        model = ShippingCutoffLog
        import_id_fields = ['id']


@admin.register(SellingPlan)
class SellingPlanAdmin(ImportExportModelAdmin):
    resource_class = SellingPlanResource
    list_display = ('name', 'interval_display', 'price_display', 'status_badge', 'created_in_django', 'needs_shopify_push', 'product_count')
    list_filter = ('billing_interval', 'is_active', 'created_in_django', 'needs_shopify_push', 'price_adjustment_type')
    search_fields = ('name', 'description', 'shopify_id')
    readonly_fields = ('shopify_id', 'shopify_selling_plan_group_id', 'created_at', 'updated_at', 'last_pushed_to_shopify', 'shopify_push_error')
    filter_horizontal = ('products',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Shopify Integration', {
            'fields': ('shopify_id', 'shopify_selling_plan_group_id')
        }),
        ('Billing Configuration', {
            'fields': ('billing_policy', 'billing_interval', 'billing_interval_count', 'billing_anchors')
        }),
        ('Pricing', {
            'fields': ('price_adjustment_type', 'price_adjustment_value')
        }),
        ('Delivery Configuration', {
            'fields': ('delivery_policy', 'delivery_interval', 'delivery_interval_count', 'delivery_anchors')
        }),
        ('Fulfillment Options', {
            'fields': ('fulfillment_exact_time', 'fulfillment_intent'),
            'classes': ('collapse',)
        }),
        ('Product Association', {
            'fields': ('products',)
        }),
        ('Sync Status', {
            'fields': ('created_in_django', 'needs_shopify_push', 'shopify_push_error', 'last_pushed_to_shopify')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['push_to_shopify', 'mark_for_push']
    
    def save_model(self, request, obj, form, change):
        """Auto-push to Shopify on create/update"""
        super().save_model(request, obj, form, change)
        
        # Auto-push to Shopify if flagged
        if obj.needs_shopify_push:
            result = subscription_sync.create_selling_plan_in_shopify(obj)
            
            if result.get('success'):
                # Refresh to get the real Shopify ID
                obj.refresh_from_db()
                self.message_user(request, f"✅ Selling Plan synced to Shopify: {obj.name} (ID: {obj.shopify_id})", level=messages.SUCCESS)
            else:
                self.message_user(request, f"⚠️ Selling Plan saved locally but Shopify sync failed: {result.get('message', 'Unknown error')}", level=messages.WARNING)
    
    def interval_display(self, obj):
        return f"Every {obj.billing_interval_count} {obj.billing_interval}(s)"
    interval_display.short_description = 'Billing Interval'
    
    def price_display(self, obj):
        if obj.price_adjustment_type == 'PERCENTAGE':
            return f"{obj.price_adjustment_value}% off"
        elif obj.price_adjustment_type == 'FIXED_AMOUNT':
            return f"${obj.price_adjustment_value} off"
        else:
            return f"${obj.price_adjustment_value}"
    price_display.short_description = 'Price Adjustment'
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>')
        return format_html('<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>')
    status_badge.short_description = 'Status'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'
    
    def push_to_shopify(self, request, queryset):
        """Push selected selling plans to Shopify"""
        results = {"successful": 0, "failed": 0, "errors": []}
        
        for plan in queryset:
            result = subscription_sync.create_selling_plan_in_shopify(plan)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{plan.name}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully pushed {results['successful']} selling plans to Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to push {results['failed']} plans. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    push_to_shopify.short_description = "📤 Push selling plans TO Shopify"
    
    def mark_for_push(self, request, queryset):
        """Mark selected plans for push to Shopify"""
        count = queryset.update(needs_shopify_push=True)
        self.message_user(request, f"✅ Marked {count} plans for push to Shopify", level=messages.SUCCESS)
    
    mark_for_push.short_description = "⚡ Mark for push to Shopify"


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(ImportExportModelAdmin):
    resource_class = CustomerSubscriptionResource
    list_display = ('customer_display', 'selling_plan_display', 'status_badge', 'next_billing_date', 'total_price', 'created_in_django', 'needs_shopify_push')
    list_filter = ('status', 'created_in_django', 'needs_shopify_push', 'billing_policy_interval', 'next_billing_date')
    search_fields = ('shopify_id', 'customer__email', 'customer__first_name', 'customer__last_name', 'notes')
    readonly_fields = ('shopify_id', 'contract_created_at', 'contract_updated_at', 'created_at', 'updated_at', 'last_pushed_to_shopify', 'last_synced_from_shopify', 'shopify_push_error', 'billing_cycle_count')
    raw_id_fields = ('customer', 'selling_plan')
    
    fieldsets = (
        ('Customer & Plan', {
            'fields': ('customer', 'selling_plan', 'status')
        }),
        ('Shopify Integration', {
            'fields': ('shopify_id', 'contract_created_at', 'contract_updated_at')
        }),
        ('Billing Schedule', {
            'fields': ('next_billing_date', 'billing_policy_interval', 'billing_policy_interval_count', 'billing_cycle_count', 'total_cycles')
        }),
        ('Delivery Schedule', {
            'fields': ('next_delivery_date', 'delivery_policy_interval', 'delivery_policy_interval_count')
        }),
        ('Pricing & Items', {
            'fields': ('line_items', 'total_price', 'currency')
        }),
        ('Delivery & Payment', {
            'fields': ('delivery_address', 'payment_method_id'),
            'classes': ('collapse',)
        }),
        ('Trial Period', {
            'fields': ('trial_end_date',),
            'classes': ('collapse',)
        }),
        ('Sync Status', {
            'fields': ('created_in_django', 'needs_shopify_push', 'shopify_push_error', 'last_pushed_to_shopify', 'last_synced_from_shopify')
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['push_to_shopify', 'update_in_shopify', 'cancel_in_shopify', 'create_billing_attempt', 'mark_for_push']
    
    def save_model(self, request, obj, form, change):
        """Auto-push to Shopify on create/update"""
        super().save_model(request, obj, form, change)
        
        # Auto-push to Shopify if flagged
        if obj.needs_shopify_push:
            # Determine if this is create or update
            if obj.shopify_id and not obj.shopify_id.startswith('temp_'):
                # Update existing subscription
                result = subscription_sync.update_subscription_in_shopify(obj)
                action = "updated"
            else:
                # Create new subscription
                result = subscription_sync.create_subscription_in_shopify(obj)
                action = "created"
            
            if result.get('success'):
                # Refresh to get the real Shopify ID
                obj.refresh_from_db()
                customer_name = f"{obj.customer.first_name} {obj.customer.last_name}" if obj.customer else "Customer"
                self.message_user(request, f"✅ Subscription {action} in Shopify for {customer_name} (ID: {obj.shopify_id})", level=messages.SUCCESS)
            else:
                self.message_user(request, f"⚠️ Subscription saved locally but Shopify sync failed: {result.get('message', 'Unknown error')}", level=messages.WARNING)
    
    def customer_display(self, obj):
        if obj.customer:
            return format_html(
                '<a href="/admin/customers/shopifycustomer/{}/change/">{} {}</a>',
                obj.customer.id,
                obj.customer.first_name,
                obj.customer.last_name
            )
        return "Unknown"
    customer_display.short_description = 'Customer'
    
    def selling_plan_display(self, obj):
        if obj.selling_plan:
            return obj.selling_plan.name
        return "No Plan"
    selling_plan_display.short_description = 'Plan'
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': 'green',
            'PAUSED': 'orange',
            'CANCELLED': 'red',
            'EXPIRED': 'gray',
            'FAILED': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'
    
    def push_to_shopify(self, request, queryset):
        """Push selected subscriptions to Shopify (create new)"""
        results = {"successful": 0, "failed": 0, "errors": []}
        
        for subscription in queryset:
            result = subscription_sync.create_subscription_in_shopify(subscription)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully pushed {results['successful']} subscriptions to Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to push {results['failed']} subscriptions. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    push_to_shopify.short_description = "📤 Push subscriptions TO Shopify (Create)"
    
    def update_in_shopify(self, request, queryset):
        """Update existing subscriptions in Shopify"""
        results = {"successful": 0, "failed": 0, "errors": []}
        
        for subscription in queryset:
            if not subscription.shopify_id:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: No Shopify ID")
                continue
            
            result = subscription_sync.update_subscription_in_shopify(subscription)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully updated {results['successful']} subscriptions in Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to update {results['failed']} subscriptions. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    update_in_shopify.short_description = "🔄 Update subscriptions IN Shopify"
    
    def cancel_in_shopify(self, request, queryset):
        """Cancel subscriptions in Shopify"""
        results = {"successful": 0, "failed": 0, "errors": []}
        
        for subscription in queryset:
            if not subscription.shopify_id:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: No Shopify ID")
                continue
            
            result = subscription_sync.cancel_subscription_in_shopify(subscription)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: {result.get('message', 'Unknown error')}")
        
        if results["successful"] > 0:
            self.message_user(request, f"✅ Successfully cancelled {results['successful']} subscriptions in Shopify", level=messages.SUCCESS)
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed to cancel {results['failed']} subscriptions. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    cancel_in_shopify.short_description = "🗑️ Cancel subscriptions IN Shopify"
    
    def create_billing_attempt(self, request, queryset):
        """Create billing attempts for subscriptions (bills customer and creates order)"""
        results = {"successful": 0, "failed": 0, "errors": []}
        
        for subscription in queryset:
            if not subscription.shopify_id:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: No Shopify ID")
                continue
            
            result = subscription_sync.create_billing_attempt(subscription)
            if result.get("success"):
                results["successful"] += 1
                order_name = result.get("order_name", "pending")
                self.message_user(request, f"✅ Billing attempt created for subscription {subscription.id}. Order: {order_name}", level=messages.SUCCESS)
            else:
                results["failed"] += 1
                results["errors"].append(f"Sub {subscription.id}: {result.get('message', 'Unknown error')}")
        
        if results["failed"] > 0:
            error_msg = f"❌ Failed {results['failed']} billing attempts. Errors: " + "; ".join(results["errors"][:3])
            self.message_user(request, error_msg, level=messages.ERROR)
    
    create_billing_attempt.short_description = "💳 Create Billing Attempts (Bill & Create Orders)"
    
    def mark_for_push(self, request, queryset):
        """Mark selected subscriptions for push"""
        count = queryset.update(needs_shopify_push=True)
        self.message_user(request, f"✅ Marked {count} subscriptions for push to Shopify", level=messages.SUCCESS)
    
    mark_for_push.short_description = "⚡ Mark for push to Shopify"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('push-pending/', self.admin_site.admin_view(self.push_pending_subscriptions), name='subscriptions_push_pending'),
        ]
        return custom_urls + urls
    
    def push_pending_subscriptions(self, request):
        """Push all subscriptions marked for push"""
        try:
            results = subscription_sync.sync_pending_subscriptions()
            if results['successful'] > 0:
                messages.success(request, f"✅ Push completed! Successful: {results['successful']}/{results['total']}")
            
            if results['failed'] > 0:
                messages.warning(request, f"❌ Failed: {results['failed']}/{results['total']}. Check sync errors.")
            
            if results['total'] == 0:
                messages.info(request, "ℹ️ No subscriptions marked for push")
        except Exception as e:
            messages.error(request, f"❌ Error during push: {str(e)}")
        
        return HttpResponseRedirect("../")
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_buttons'] = format_html(
            '<a class="button" href="push-pending/">📤 Push Pending TO Shopify</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(SubscriptionBillingAttempt)
class SubscriptionBillingAttemptAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionBillingAttemptResource
    list_display = ('subscription_display', 'status_badge', 'amount_display', 'attempted_at', 'completed_at')
    list_filter = ('status', 'attempted_at', 'currency')
    search_fields = ('shopify_id', 'shopify_order_id', 'error_message', 'subscription__customer__email')
    readonly_fields = ('shopify_id', 'shopify_order_id', 'attempted_at', 'completed_at', 'created_at')
    date_hierarchy = 'attempted_at'
    
    fieldsets = (
        ('Subscription', {
            'fields': ('subscription', 'shopify_id')
        }),
        ('Billing Info', {
            'fields': ('status', 'amount', 'currency', 'shopify_order_id')
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_code'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('attempted_at', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subscription_display(self, obj):
        return str(obj.subscription)
    subscription_display.short_description = 'Subscription'
    
    def status_badge(self, obj):
        colors = {
            'SUCCESS': 'green',
            'FAILED': 'red',
            'PENDING': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'
    
    def amount_display(self, obj):
        return f"${obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'


@admin.register(SubscriptionSyncLog)
class SubscriptionSyncLogAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionSyncLogResource
    list_display = ('operation_type', 'status_badge', 'stats_display', 'started_at', 'duration')
    list_filter = ('operation_type', 'status', 'started_at')
    search_fields = ('error_message',)
    readonly_fields = ('started_at', 'completed_at')
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation_type', 'status')
        }),
        ('Statistics', {
            'fields': ('subscriptions_processed', 'subscriptions_successful', 'subscriptions_failed')
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'in_progress': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'
    
    def stats_display(self, obj):
        return format_html(
            'Processed: {} | ✅ Success: {} | ❌ Failed: {}',
            obj.subscriptions_processed,
            obj.subscriptions_successful,
            obj.subscriptions_failed
        )
    stats_display.short_description = 'Statistics'
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.2f}s"
        return "In Progress" if obj.status == 'in_progress' else "N/A"
    duration.short_description = 'Duration'


# =============================================================================
# ADDRESS MANAGEMENT ADMIN INTERFACES
# =============================================================================

@admin.register(SubscriptionAddress)
class SubscriptionAddressAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionAddressResource
    """Admin for Primary Subscription Addresses - editable anytime, changes propagate to unshipped orders"""
    
    list_display = ('customer_email', 'address_display', 'city', 'province', 'country', 'is_validated', 'last_updated', 'needs_sync_badge')
    list_filter = ('country', 'province', 'is_validated', 'needs_shopify_sync', 'last_updated')
    search_fields = ('customer__email', 'first_name', 'last_name', 'address1', 'city')
    readonly_fields = ('created_at', 'last_updated', 'last_shopify_sync')
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Address Details', {
            'fields': ('first_name', 'last_name', 'company', 'address1', 'address2', 'city', 'province', 'country', 'zip_code', 'phone')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validation_notes')
        }),
        ('Change Tracking', {
            'fields': ('updated_by', 'last_updated', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Shopify Sync', {
            'fields': ('needs_shopify_sync', 'last_shopify_sync'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['validate_addresses', 'sync_to_shopify', 'propagate_to_unshipped']
    
    def customer_email(self, obj):
        return obj.customer.email
    customer_email.short_description = 'Customer Email'
    customer_email.admin_order_field = 'customer__email'
    
    def address_display(self, obj):
        return f"{obj.first_name} {obj.last_name} - {obj.address1}"
    address_display.short_description = 'Address'
    
    def needs_sync_badge(self, obj):
        if obj.needs_shopify_sync:
            return format_html('<span style="color: orange;">⚡ Needs Sync</span>')
        return format_html('<span style="color: green;">✅ Synced</span>')
    needs_sync_badge.short_description = 'Sync Status'
    
    def validate_addresses(self, request, queryset):
        """Validate selected addresses with shipping carriers"""
        count = 0
        for address in queryset:
            # Here you would integrate with shipping carrier APIs for validation
            address.is_validated = True
            address.validation_notes = "Validated via admin action"
            address.updated_by = request.user.username
            address.save()
            count += 1
        
        self.message_user(request, f"Validated {count} addresses", level=messages.SUCCESS)
    validate_addresses.short_description = "✅ Validate selected addresses"
    
    def sync_to_shopify(self, request, queryset):
        """Sync addresses to Shopify subscriptions"""
        count = 0
        for address in queryset:
            # Mark for sync - actual sync would happen in background task
            address.needs_shopify_sync = True
            address.save()
            count += 1
        
        self.message_user(request, f"Marked {count} addresses for Shopify sync", level=messages.SUCCESS)
    sync_to_shopify.short_description = "📤 Sync to Shopify"
    
    def propagate_to_unshipped(self, request, queryset):
        """Propagate address changes to unshipped orders"""
        count = 0
        for address in queryset:
            address._propagate_to_unshipped_orders()
            count += 1
        
        self.message_user(request, f"Propagated {count} addresses to unshipped orders", level=messages.SUCCESS)
    propagate_to_unshipped.short_description = "🔄 Propagate to unshipped orders"


@admin.register(OrderAddressOverride)
class OrderAddressOverrideAdmin(ImportExportModelAdmin):
    resource_class = OrderAddressOverrideResource
    """Admin for Per-Order Address Overrides - Edit address for this delivery only"""
    
    list_display = ('order_name', 'customer_email', 'address_display', 'city', 'is_temporary', 'reason', 'created_at')
    list_filter = ('is_temporary', 'country', 'province', 'needs_shopify_sync', 'created_at')
    search_fields = ('order__name', 'order__customer_email', 'first_name', 'last_name', 'address1', 'reason')
    readonly_fields = ('created_at', 'updated_at', 'last_shopify_sync')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Override Address Details', {
            'fields': ('first_name', 'last_name', 'company', 'address1', 'address2', 'city', 'province', 'country', 'zip_code', 'phone')
        }),
        ('Override Details', {
            'fields': ('reason', 'is_temporary', 'created_by')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Shopify Sync', {
            'fields': ('needs_shopify_sync', 'last_shopify_sync'),
            'classes': ('collapse',)
        }),
    )
    
    def order_name(self, obj):
        return obj.order.name
    order_name.short_description = 'Order'
    order_name.admin_order_field = 'order__name'
    
    def customer_email(self, obj):
        return obj.order.customer_email
    customer_email.short_description = 'Customer'
    customer_email.admin_order_field = 'order__customer_email'
    
    def address_display(self, obj):
        return f"{obj.first_name} {obj.last_name} - {obj.address1}"
    address_display.short_description = 'Override Address'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Creating new override
            form.base_fields['created_by'].initial = request.user.username
        return form


@admin.register(ProductShippingConfig)
class ProductShippingConfigAdmin(ImportExportModelAdmin):
    resource_class = ProductShippingConfigResource
    """Admin for Per-Product Shipping Configuration - Cutoff logic and shipping settings"""
    
    list_display = ('product_title', 'cutoff_days', 'reminder_days', 'processing_days', 'international_shipping', 'special_handling')
    list_filter = ('cutoff_days', 'international_shipping', 'special_handling', 'created_at')
    search_fields = ('product__title', 'handling_notes')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Product', {
            'fields': ('product',)
        }),
        ('Cutoff Configuration', {
            'fields': ('cutoff_days', 'reminder_days'),
            'description': 'Configure when orders are cut off and when reminders are sent'
        }),
        ('Shipping Details', {
            'fields': ('processing_days', 'estimated_transit_days')
        }),
        ('Special Handling', {
            'fields': ('special_handling', 'handling_notes')
        }),
        ('International Shipping', {
            'fields': ('international_shipping', 'restricted_countries')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['set_standard_cutoff', 'enable_international', 'disable_international']
    
    def product_title(self, obj):
        return obj.product.title
    product_title.short_description = 'Product'
    product_title.admin_order_field = 'product__title'
    
    def set_standard_cutoff(self, request, queryset):
        """Set standard 7-day cutoff for selected products"""
        count = queryset.update(cutoff_days=7, reminder_days=14)
        self.message_user(request, f"Set standard cutoff for {count} products", level=messages.SUCCESS)
    set_standard_cutoff.short_description = "⏰ Set standard 7-day cutoff"
    
    def enable_international(self, request, queryset):
        """Enable international shipping for selected products"""
        count = queryset.update(international_shipping=True)
        self.message_user(request, f"Enabled international shipping for {count} products", level=messages.SUCCESS)
    enable_international.short_description = "🌍 Enable international shipping"
    
    def disable_international(self, request, queryset):
        """Disable international shipping for selected products"""
        count = queryset.update(international_shipping=False)
        self.message_user(request, f"Disabled international shipping for {count} products", level=messages.SUCCESS)
    disable_international.short_description = "🚫 Disable international shipping"


@admin.register(ShippingCutoffLog)
class ShippingCutoffLogAdmin(ImportExportModelAdmin):
    resource_class = ShippingCutoffLogResource
    """Admin for Shipping Cutoff Logs - Track notifications and reminders"""
    
    list_display = ('order_name', 'customer_email', 'notification_type', 'cutoff_date', 'delivery_status', 'sent_at')
    list_filter = ('notification_type', 'delivery_status', 'email_sent', 'sms_sent', 'sent_at')
    search_fields = ('order__name', 'customer__email', 'subject', 'message')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('order', 'customer', 'notification_type', 'cutoff_date')
        }),
        ('Content', {
            'fields': ('subject', 'message')
        }),
        ('Delivery Status', {
            'fields': ('delivery_status', 'email_sent', 'sms_sent', 'sent_at')
        }),
    )
    
    def order_name(self, obj):
        return obj.order.name
    order_name.short_description = 'Order'
    order_name.admin_order_field = 'order__name'
    
    def customer_email(self, obj):
        return obj.customer.email
    customer_email.short_description = 'Customer'
    customer_email.admin_order_field = 'customer__email'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
