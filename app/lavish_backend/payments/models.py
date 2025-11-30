"""
Shopify Payments Models
Handles balance transactions, payouts, disputes, and bank accounts
"""

from django.db import models
from django.utils import timezone


class ShopifyPaymentsAccount(models.Model):
    """Shopify Payments account information"""
    shopify_id = models.CharField(max_length=255, unique=True)
    account_opener_name = models.CharField(max_length=255, blank=True, null=True)
    activated = models.BooleanField(default=False)
    country = models.CharField(max_length=2)
    default_currency = models.CharField(max_length=3)
    onboardable = models.BooleanField(default=False)
    payout_statement_descriptor = models.CharField(max_length=255, blank=True)
    charge_statement_descriptor = models.CharField(max_length=255, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Shopify Payments Account'
        verbose_name_plural = 'Shopify Payments Accounts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payments Account - {self.country} ({self.default_currency})"


class ShopifyBalanceTransaction(models.Model):
    """Balance transactions for Shopify Payments account"""
    
    TRANSACTION_TYPES = [
        ('charge', 'Charge'),
        ('refund', 'Refund'),
        ('dispute', 'Dispute'),
        ('reserve', 'Reserve'),
        ('adjustment', 'Adjustment'),
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('payout', 'Payout'),
        ('payout_failure', 'Payout Failure'),
        ('payout_cancellation', 'Payout Cancellation'),
    ]
    
    SOURCE_TYPES = [
        ('charge', 'Charge'),
        ('refund', 'Refund'),
        ('dispute', 'Dispute'),
        ('reserve', 'Reserve'),
        ('adjustment', 'Adjustment'),
        ('payout', 'Payout'),
    ]
    
    shopify_id = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(
        ShopifyPaymentsAccount,
        on_delete=models.CASCADE,
        related_name='balance_transactions'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    test = models.BooleanField(default=False)
    
    # Amounts
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Source information
    source_id = models.CharField(max_length=255, blank=True, null=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES, blank=True, null=True)
    source_order_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Associated records
    associated_order_id = models.CharField(max_length=255, blank=True, null=True)
    associated_payout_id = models.CharField(max_length=255, blank=True, null=True)
    associated_payout_status = models.CharField(max_length=50, blank=True, null=True)
    
    # Adjustments
    adjustment_reason = models.TextField(blank=True, null=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Balance Transaction'
        verbose_name_plural = 'Balance Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_type', 'created_at']),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['associated_payout_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type.title()} - {self.currency_code} {self.amount}"


class ShopifyPayout(models.Model):
    """Payouts from Shopify Payments to bank account"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_transit', 'In Transit'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    shopify_id = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(
        ShopifyPaymentsAccount,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    
    # Payout details
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    
    # Bank account (simplified - can be expanded)
    bank_account_id = models.CharField(max_length=255, blank=True)
    
    # Dates
    payout_date = models.DateField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'
        ordering = ['-payout_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'payout_date']),
            models.Index(fields=['currency_code']),
        ]
    
    def __str__(self):
        return f"Payout {self.status.title()} - {self.currency_code} {self.amount}"


class ShopifyBankAccount(models.Model):
    """Bank accounts configured for Shopify Payments"""
    
    STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('pending', 'Pending'),
        ('errored', 'Errored'),
    ]
    
    shopify_id = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(
        ShopifyPaymentsAccount,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    
    # Bank details (masked for security)
    bank_name = models.CharField(max_length=255, blank=True)
    account_number_last4 = models.CharField(max_length=4, blank=True)
    routing_number = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=3)
    country = models.CharField(max_length=2)
    
    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.bank_name} - ****{self.account_number_last4}"


class ShopifyDispute(models.Model):
    """Disputes on Shopify Payments transactions"""
    
    STATUS_CHOICES = [
        ('needs_response', 'Needs Response'),
        ('under_review', 'Under Review'),
        ('charge_refunded', 'Charge Refunded'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    
    TYPE_CHOICES = [
        ('chargeback', 'Chargeback'),
        ('inquiry', 'Inquiry'),
    ]
    
    REASON_CHOICES = [
        ('bank_cannot_process', 'Bank Cannot Process'),
        ('credit_not_processed', 'Credit Not Processed'),
        ('customer_initiated', 'Customer Initiated'),
        ('debit_not_authorized', 'Debit Not Authorized'),
        ('duplicate', 'Duplicate'),
        ('fraudulent', 'Fraudulent'),
        ('general', 'General'),
        ('incorrect_account_details', 'Incorrect Account Details'),
        ('insufficient_funds', 'Insufficient Funds'),
        ('product_not_received', 'Product Not Received'),
        ('product_unacceptable', 'Product Unacceptable'),
        ('subscription_canceled', 'Subscription Canceled'),
        ('unrecognized', 'Unrecognized'),
    ]
    
    shopify_id = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(
        ShopifyPaymentsAccount,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    
    # Dispute details
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    dispute_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='chargeback')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    network_reason_code = models.CharField(max_length=50, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    
    # Associated order
    order_id = models.CharField(max_length=255, blank=True)
    
    # Dates
    initiated_at = models.DateTimeField(null=True, blank=True)
    evidence_due_by = models.DateTimeField(null=True, blank=True)
    evidence_sent_on = models.DateTimeField(null=True, blank=True)
    finalized_on = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
        ordering = ['-initiated_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'initiated_at']),
            models.Index(fields=['reason']),
            models.Index(fields=['dispute_type']),
        ]
    
    def __str__(self):
        return f"Dispute {self.status.replace('_', ' ').title()} - {self.currency_code} {self.amount}"


class ShopifyDisputeEvidence(models.Model):
    """Evidence submitted for disputes"""
    
    shopify_id = models.CharField(max_length=255, unique=True)
    dispute = models.OneToOneField(
        ShopifyDispute,
        on_delete=models.CASCADE,
        related_name='evidence'
    )
    
    # Evidence fields (simplified - can be expanded based on needs)
    submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dispute Evidence'
        verbose_name_plural = 'Dispute Evidence'
    
    def __str__(self):
        return f"Evidence for Dispute {self.dispute.shopify_id.split('/')[-1]}"


class ShopifyPaymentsSyncLog(models.Model):
    """Log of payment data sync operations"""
    
    OPERATION_TYPES = [
        ('full_sync', 'Full Sync'),
        ('balance_transactions', 'Balance Transactions'),
        ('payouts', 'Payouts'),
        ('disputes', 'Disputes'),
        ('bank_accounts', 'Bank Accounts'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Statistics
    items_processed = models.IntegerField(default=0)
    items_created = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    
    class Meta:
        verbose_name = 'Payments Sync Log'
        verbose_name_plural = 'Payments Sync Logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.operation_type} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"


class ShopifyFinanceKYC(models.Model):
    """KYC (Know Your Customer) information for Shopify Payments account"""
    
    BUSINESS_TYPE_CHOICES = [
        ('corporation', 'Corporation'),
        ('free_zone_establishment', 'Free Zone Establishment'),
        ('free_zone_llc', 'Free Zone LLC'),
        ('government', 'Government'),
        ('incorporated_partnership', 'Incorporated Partnership'),
        ('individual', 'Individual'),
        ('llc', 'LLC'),
        ('non_profit', 'Non Profit'),
        ('non_profit_incorporated', 'Non Profit Incorporated'),
        ('non_profit_registered_charity', 'Non Profit Registered Charity'),
        ('non_profit_unincorporated', 'Non Profit Unincorporated'),
        ('non_profit_unincorporated_association', 'Non Profit Unincorporated Association'),
        ('not_set', 'Not Set'),
        ('partnership', 'Partnership'),
        ('private_corporation', 'Private Corporation'),
        ('private_multi_member_llc', 'Private Multi Member LLC'),
        ('private_partnership', 'Private Partnership'),
        ('private_single_member_llc', 'Private Single Member LLC'),
        ('private_unincorporated_association', 'Private Unincorporated Association'),
        ('public_company', 'Public Company'),
        ('public_corporation', 'Public Corporation'),
        ('public_partnership', 'Public Partnership'),
        ('sole_establishment', 'Sole Establishment'),
        ('sole_prop', 'Sole Proprietorship'),
        ('unincorporated_partnership', 'Unincorporated Partnership'),
    ]
    
    TAX_ID_TYPE_CHOICES = [
        ('ein', 'EIN - Employer Identification Number'),
        ('ssn', 'SSN - Social Security Number'),
        ('abn', 'ABN - Australian Business Number'),
        ('acn', 'ACN - Australian Company Number'),
        ('gst', 'GST - Goods and Services Tax'),
        ('vat', 'VAT - Value Added Tax'),
        ('other', 'Other'),
    ]
    
    account = models.OneToOneField(
        ShopifyPaymentsAccount,
        on_delete=models.CASCADE,
        related_name='kyc_info'
    )
    
    # Business Information
    legal_name = models.CharField(max_length=255, blank=True)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES, blank=True)
    
    # Business Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zone = models.CharField(max_length=100, blank=True)  # State/Province
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    
    # Industry Information
    industry_category = models.CharField(max_length=255, blank=True)
    industry_category_label = models.CharField(max_length=255, blank=True)
    industry_code = models.IntegerField(null=True, blank=True)  # MCC code
    industry_subcategory_label = models.CharField(max_length=255, blank=True)
    
    # Shop Owner Information
    owner_email = models.EmailField(blank=True)
    owner_first_name = models.CharField(max_length=100, blank=True)
    owner_last_name = models.CharField(max_length=100, blank=True)
    owner_phone = models.CharField(max_length=50, blank=True)
    
    # Tax Identification
    tax_id_type = models.CharField(max_length=50, choices=TAX_ID_TYPE_CHOICES, blank=True)
    tax_id_value = models.CharField(max_length=255, blank=True)  # Encrypted/masked in production
    
    # Metadata
    store_domain = models.CharField(max_length=255, default='7fa66c-ac.myshopify.com')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Finance KYC Information'
        verbose_name_plural = 'Finance KYC Information'
    
    def __str__(self):
        return f"KYC - {self.legal_name or 'Unnamed Business'} ({self.country})"
