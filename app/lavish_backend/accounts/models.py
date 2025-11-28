from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

# IndustryType model to define the type of industry a company belongs to
class IndustryType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CompanyRole(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Company(models.Model):
    logo = models.ImageField(upload_to='images/company', blank=True, null=True)
    name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=50)
    industry_type = models.ForeignKey(IndustryType, on_delete=models.SET_NULL, null=True)
    employee_count = models.CharField(max_length=10)
    website = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    suburb = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100)
    contact_email = models.EmailField(max_length=150, unique=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    business_category = models.CharField(max_length=100, blank=True, null=True)
    company_registration_number = models.CharField(max_length=50, blank=True, null=True)
    jurisdiction_code = models.CharField(max_length=50, blank=True, null=True)
    incorporation_date = models.DateField(blank=True, null=True)
    asic_extract = models.FileField(upload_to='documents/business_verification', blank=True, null=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_companies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

    def get_photo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        else:
            return "/static/images/users/multi-user.jpg"

    def is_dirty_for_fields(self, field_names):
        """
        Check if any of the specified fields have been modified.
        Used to determine if verification status needs to be reset.
        
        Args:
            field_names: List of field names to check for changes
            
        Returns:
            bool: True if any of the specified fields have been modified
        """
        if not self.pk:
            return True  # New instance, so it's dirty
            
        try:
            # Get the original instance from DB
            original = Company.objects.get(pk=self.pk)
            
            # Check each field
            for field_name in field_names:
                original_value = getattr(original, field_name)
                current_value = getattr(self, field_name)
                
                # Check if the field has changed
                if original_value != current_value:
                    return True
                    
            return False
        except Company.DoesNotExist:
            return True  # Can't find original, assume it's dirty


class CustomUser(AbstractUser):
    fullname = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True)
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)
    suburb = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    email_verified = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)
    face_login_enabled = models.BooleanField(default=False, help_text="Whether to use facial recognition for login")
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_company_admin = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default='UTC', blank=True)
    last_url = models.CharField(max_length=255, blank=True, null=True, help_text="Last URL visited before logout")
    session_data = models.JSONField(blank=True, null=True, help_text="Additional session data to restore user state")
    last_activity = models.DateTimeField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username


class UserSession(models.Model):
    """
    Model to track user sessions for auditing and security
    """
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='sessions'
    )
    session_key = models.CharField(max_length=128, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    login_method = models.CharField(max_length=20, choices=(
        ('password', 'Password'),
        ('facial', 'Facial Recognition'),
        ('2fa', 'Two-Factor Authentication'),
        ('social', 'Social Login'),
    ), default='password')
    is_active = models.BooleanField(default=True)
    expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.created_at})"


class CompanyStaff(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.ForeignKey(CompanyRole, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.fullname} - {self.role.name} at {self.company.name}"


class BankDetail(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bank_details"
    )
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_holder_name = models.CharField(max_length=255)
    iban = models.CharField(max_length=34, blank=True, null=True)
    swift_code = models.CharField(max_length=11, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class CardDetail(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="card_details"
    )
    card_number = models.CharField(max_length=20)
    cardholder_name = models.CharField(max_length=255)
    expiry_date = models.DateField()
    cvv = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Card ending in {self.card_number[-4:]}"


class PayID(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pay_ids")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class StoragePlan(models.Model):
    """Storage plan subscription options"""
    BILLING_CYCLE_CHOICES = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    
    name = models.CharField(max_length=50)
    storage_limit = models.BigIntegerField(help_text="Storage limit in bytes")
    price_monthly = models.DecimalField(max_digits=6, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def get_formatted_storage(self):
        """Return human-readable storage size"""
        size_bytes = self.storage_limit
        
        # Define size units and their thresholds
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
            
        # Return formatted size with appropriate unit
        return f"{size_bytes:.0f} {units[i]}"
    
    class Meta:
        ordering = ['storage_limit']


class UserSubscription(models.Model):
    """User's storage subscription"""
    SUBSCRIPTION_STATUS_CHOICES = (
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='storage_subscription')
    plan = models.ForeignKey(StoragePlan, on_delete=models.SET_NULL, null=True, related_name='subscribers')
    billing_cycle = models.CharField(max_length=10, choices=StoragePlan.BILLING_CYCLE_CHOICES, default='monthly')
    status = models.CharField(max_length=10, choices=SUBSCRIPTION_STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.plan.name if self.plan else 'No'} Plan"
    
    def get_storage_usage(self):
        from drive.models import Document
        total_size = 0
        user_files = Document.objects.filter(user=self.user)
        for file in user_files:
            if file.file and hasattr(file.file, 'size'):
                total_size += file.file.size
        return total_size
    
    def get_storage_percentage(self):
        """Calculate storage usage as percentage"""
        if not self.plan:
            return 100  # Default to 100% if no plan
        
        usage = self.get_storage_usage()
        percentage = (usage / self.plan.storage_limit) * 100
        return min(percentage, 100)  # Cap at 100%
    
    def get_formatted_usage(self):
        size_bytes = self.get_storage_usage()
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def is_storage_full(self):
        """Check if user has reached storage limit"""
        if not self.plan:
            return True
        
        return self.get_storage_usage() >= self.plan.storage_limit
    
    class Meta:
        ordering = ['-start_date']


class SubscriptionTransaction(models.Model):
    """Record of subscription payments"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.subscription.user.username} - {self.amount} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-transaction_date']


class FacialIdentity(models.Model):
    """
    Links a user account to a face stored in the face recognition system.
    This allows facial login as an alternative to password or MFA.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='facial_identity')
    face_id = models.IntegerField(help_text="ID of the face in the face detection database")
    face_name = models.CharField(max_length=255, help_text="Name identifier in face detection database")
    face_image_path = models.CharField(max_length=255, blank=True, null=True, help_text="Path relative to MEDIA_ROOT, e.g. face_images/face_53_12345.jpg")
    enabled = models.BooleanField(default=True, help_text="Whether facial login is enabled for this user")
    require_smile = models.BooleanField(default=False, help_text="Whether the user must smile to authenticate")
    min_confidence = models.FloatField(default=75.0, help_text="Minimum confidence percentage for facial recognition (0-100)")
    date_registered = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Facial identity for {self.user.username}"
    
    def update_last_used(self):
        """Update the last_used timestamp to now"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class FaceDetection(models.Model):
    """
    Model for storing detected faces from the face detection system
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    image_path = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    face_hash = models.CharField(max_length=255, unique=True)
    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    meta_data = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Face: {self.name or 'Unknown'} ({self.id})"
    
    class Meta:
        verbose_name = "Face Detection"
        verbose_name_plural = "Face Detections"
        ordering = ['-timestamp']


class DetectionEvent(models.Model):
    """
    Model for tracking each face detection event
    """
    face = models.ForeignKey(FaceDetection, on_delete=models.CASCADE, related_name='detection_events')
    timestamp = models.DateTimeField()
    detection_type = models.CharField(max_length=50)
    
    def __str__(self):
        return f"Detection of {self.face.name or 'Unknown'} on {self.timestamp}"
    
    class Meta:
        verbose_name = "Detection Event"
        verbose_name_plural = "Detection Events"
        ordering = ['-timestamp']


class CompanySite(models.Model):
    """Model for company sites/locations - can be used across all apps"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    suburb = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Australia')
    contact_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
    class Meta:
        unique_together = ['company', 'name']
        ordering = ['company', 'name']
        verbose_name = "Company Site"
        verbose_name_plural = "Company Sites"
