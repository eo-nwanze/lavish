"""
Shopify Payments Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import (
    ShopifyPaymentsAccount,
    ShopifyBalanceTransaction,
    ShopifyPayout,
    ShopifyBankAccount,
    ShopifyDispute,
    ShopifyDisputeEvidence,
    ShopifyFinanceKYC,
    ShopifyPaymentsSyncLog
)


@admin.register(ShopifyPaymentsAccount)
class ShopifyPaymentsAccountAdmin(admin.ModelAdmin):
    list_display = ('country', 'default_currency', 'activated', 'onboardable', 'created_at')
    list_filter = ('activated', 'country', 'default_currency')
    search_fields = ('account_opener_name', 'country')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Account Information', {
            'fields': ('shopify_id', 'account_opener_name', 'activated', 'onboardable')
        }),
        ('Location & Currency', {
            'fields': ('country', 'default_currency')
        }),
        ('Statement Descriptors', {
            'fields': ('payout_statement_descriptor', 'charge_statement_descriptor')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShopifyBalanceTransaction)
class ShopifyBalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ('shopify_id_short', 'transaction_type', 'amount_display', 'net_amount_display', 
                    'fee_display', 'test', 'created_at')
    list_filter = ('transaction_type', 'test', 'currency_code', 'source_type', 'created_at')
    search_fields = ('shopify_id', 'source_id', 'associated_order_id', 'associated_payout_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('shopify_id', 'account', 'transaction_type', 'test')
        }),
        ('Amounts', {
            'fields': ('amount', 'currency_code', 'fee_amount', 'net_amount')
        }),
        ('Source Information', {
            'fields': ('source_type', 'source_id', 'source_order_transaction_id')
        }),
        ('Associated Records', {
            'fields': ('associated_order_id', 'associated_payout_id', 'associated_payout_status')
        }),
        ('Adjustments', {
            'fields': ('adjustment_reason',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def shopify_id_short(self, obj):
        return obj.shopify_id.split('/')[-1] if '/' in obj.shopify_id else obj.shopify_id
    shopify_id_short.short_description = 'ID'
    
    def amount_display(self, obj):
        color = 'green' if obj.amount >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, obj.currency_code, obj.amount
        )
    amount_display.short_description = 'Amount'
    
    def net_amount_display(self, obj):
        return f"{obj.currency_code} {obj.net_amount}"
    net_amount_display.short_description = 'Net'
    
    def fee_display(self, obj):
        return f"{obj.currency_code} {obj.fee_amount}"
    fee_display.short_description = 'Fee'


@admin.register(ShopifyPayout)
class ShopifyPayoutAdmin(admin.ModelAdmin):
    list_display = ('shopify_id_short', 'status_badge', 'amount_display', 'payout_date', 'created_at')
    list_filter = ('status', 'currency_code', 'payout_date', 'created_at')
    search_fields = ('shopify_id', 'bank_account_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    date_hierarchy = 'payout_date'
    
    fieldsets = (
        ('Payout Details', {
            'fields': ('shopify_id', 'account', 'status', 'payout_date')
        }),
        ('Amount', {
            'fields': ('amount', 'currency_code')
        }),
        ('Bank Account', {
            'fields': ('bank_account_id',)
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def shopify_id_short(self, obj):
        return obj.shopify_id.split('/')[-1] if '/' in obj.shopify_id else obj.shopify_id
    shopify_id_short.short_description = 'ID'
    
    def status_badge(self, obj):
        colors = {
            'scheduled': 'blue',
            'in_transit': 'orange',
            'paid': 'green',
            'failed': 'red',
            'canceled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'
    
    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{} {}</span>',
            obj.currency_code, obj.amount
        )
    amount_display.short_description = 'Amount'


@admin.register(ShopifyBankAccount)
class ShopifyBankAccountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_number_display', 'currency', 'country', 'status_badge', 'created_at')
    list_filter = ('status', 'currency', 'country', 'created_at')
    search_fields = ('bank_name', 'account_number_last4', 'shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Bank Details', {
            'fields': ('shopify_id', 'account', 'bank_name', 'account_number_last4', 'routing_number')
        }),
        ('Location & Currency', {
            'fields': ('currency', 'country', 'status')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_number_display(self, obj):
        return f"****{obj.account_number_last4}"
    account_number_display.short_description = 'Account Number'
    
    def status_badge(self, obj):
        colors = {
            'verified': 'green',
            'pending': 'orange',
            'errored': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.title()
        )
    status_badge.short_description = 'Status'


@admin.register(ShopifyDispute)
class ShopifyDisputeAdmin(admin.ModelAdmin):
    list_display = ('shopify_id_short', 'status_badge', 'type_badge', 'reason_display', 'amount_display', 
                    'initiated_at', 'evidence_due_by')
    list_filter = ('status', 'dispute_type', 'reason', 'currency_code', 'initiated_at')
    search_fields = ('shopify_id', 'order_id', 'network_reason_code')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    date_hierarchy = 'initiated_at'
    
    fieldsets = (
        ('Dispute Details', {
            'fields': ('shopify_id', 'account', 'status', 'dispute_type', 'reason', 'network_reason_code')
        }),
        ('Amount', {
            'fields': ('amount', 'currency_code')
        }),
        ('Associated Order', {
            'fields': ('order_id',)
        }),
        ('Important Dates', {
            'fields': ('initiated_at', 'evidence_due_by', 'evidence_sent_on', 'finalized_on')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def shopify_id_short(self, obj):
        return obj.shopify_id.split('/')[-1] if '/' in obj.shopify_id else obj.shopify_id
    shopify_id_short.short_description = 'ID'
    
    def status_badge(self, obj):
        colors = {
            'needs_response': 'red',
            'under_review': 'orange',
            'charge_refunded': 'blue',
            'won': 'green',
            'lost': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'
    
    def type_badge(self, obj):
        colors = {
            'chargeback': 'red',
            'inquiry': 'orange',
        }
        color = colors.get(obj.dispute_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.dispute_type.title()
        )
    type_badge.short_description = 'Type'
    
    def reason_display(self, obj):
        return obj.reason.replace('_', ' ').title()
    reason_display.short_description = 'Reason'
    
    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: red;">{} {}</span>',
            obj.currency_code, obj.amount
        )
    amount_display.short_description = 'Amount'


@admin.register(ShopifyDisputeEvidence)
class ShopifyDisputeEvidenceAdmin(admin.ModelAdmin):
    list_display = ('dispute_id_short', 'submitted', 'submitted_at', 'created_at')
    list_filter = ('submitted', 'submitted_at')
    search_fields = ('shopify_id', 'dispute__shopify_id')
    readonly_fields = ('shopify_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Evidence Details', {
            'fields': ('shopify_id', 'dispute', 'submitted', 'submitted_at')
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def dispute_id_short(self, obj):
        return obj.dispute.shopify_id.split('/')[-1] if obj.dispute else 'N/A'
    dispute_id_short.short_description = 'Dispute ID'


@admin.register(ShopifyFinanceKYC)
class ShopifyFinanceKYCAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'business_type', 'country', 'owner_name', 'industry_display', 'created_at')
    list_filter = ('business_type', 'country', 'tax_id_type')
    search_fields = ('legal_name', 'owner_email', 'owner_first_name', 'owner_last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Business Information', {
            'fields': ('account', 'legal_name', 'business_type')
        }),
        ('Business Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'zone', 'postal_code', 'country')
        }),
        ('Industry Information', {
            'fields': ('industry_category', 'industry_category_label', 'industry_code', 'industry_subcategory_label')
        }),
        ('Shop Owner', {
            'fields': ('owner_first_name', 'owner_last_name', 'owner_email', 'owner_phone')
        }),
        ('Tax Identification', {
            'fields': ('tax_id_type', 'tax_id_value'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('store_domain', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def owner_name(self, obj):
        return f"{obj.owner_first_name} {obj.owner_last_name}".strip() or "N/A"
    owner_name.short_description = 'Owner'
    
    def industry_display(self, obj):
        if obj.industry_code:
            return f"{obj.industry_category_label} ({obj.industry_code})"
        return obj.industry_category_label or "N/A"
    industry_display.short_description = 'Industry'


@admin.register(ShopifyPaymentsSyncLog)
class ShopifyPaymentsSyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation_type', 'status_badge', 'stats_display', 'started_at', 'duration')
    list_filter = ('operation_type', 'status', 'started_at')
    search_fields = ('error_message',)
    readonly_fields = ('started_at', 'completed_at', 'duration')
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation_type', 'status')
        }),
        ('Statistics', {
            'fields': ('items_processed', 'items_created', 'items_updated', 'items_failed')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('store_domain',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
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
        return f"✓ {obj.items_created} | ↻ {obj.items_updated} | ✗ {obj.items_failed}"
    stats_display.short_description = 'Stats (Created | Updated | Failed)'
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            seconds = delta.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            else:
                minutes = seconds / 60
                return f"{minutes:.1f}m"
        return "In progress..." if obj.status == 'in_progress' else "N/A"
    duration.short_description = 'Duration'
    
    def has_add_permission(self, request):
        return False  # Sync logs are created automatically
