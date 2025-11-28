from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Company, IndustryType, CompanyRole, CompanyStaff, BankDetail, CardDetail, PayID, UserSession, CompanySite


class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'fullname', 'gender', 'is_staff', 'is_active',
        'email_verified', 'mfa_enabled', 'company', 'is_company_admin'
    )
    list_filter = (
        'is_staff', 'is_active', 'email_verified', 'mfa_enabled', 'gender',
        'company', 'date_joined'
    )
    search_fields = ('username', 'email', 'fullname', 'phone', 'address')
    ordering = ('-date_joined', 'username')
    list_per_page = 10

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'fullname', 'email', 'phone', 'address', 'suburb', 'state',
                'country', 'gender', 'dob', 'company'
            )
        }),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('MFA Information'), {'fields': ('email_verified', 'mfa_enabled', 'otp_secret')}),
        (_('Company Permissions'), {'fields': ('is_company_admin',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'company', 'is_company_admin'),
        }),
    )

    actions = [
        'activate_users', 'deactivate_users', 'enable_mfa', 'disable_mfa',
        'set_as_company_admin', 'remove_company_admin', 'reset_mfa'
    ]
    readonly_fields = ('date_joined', 'last_login')

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Deactivate selected users"

    def enable_mfa(self, request, queryset):
        queryset.update(mfa_enabled=True)
    enable_mfa.short_description = "Enable MFA for selected users"

    def disable_mfa(self, request, queryset):
        queryset.update(mfa_enabled=False)
    disable_mfa.short_description = "Disable MFA for selected users"

    def set_as_company_admin(self, request, queryset):
        queryset.update(is_company_admin=True)
    set_as_company_admin.short_description = "Set as Company Admin"

    def remove_company_admin(self, request, queryset):
        queryset.update(is_company_admin=False)
    remove_company_admin.short_description = "Remove Company Admin Rights"

    def reset_mfa(self, request, queryset):
        queryset.update(otp_secret=None, mfa_enabled=False)
    reset_mfa.short_description = "Reset MFA for selected users"


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry_type', 'employee_count', 'website', 'contact_email', 'created_by')
    search_fields = ('name', 'industry_type__name', 'contact_email')
    list_filter = ('industry_type', 'country')
    list_per_page = 10


@admin.register(CompanyRole)
class CompanyRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_per_page = 10


@admin.register(CompanyStaff)
class CompanyStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'is_active')
    search_fields = ('user__fullname', 'company__name', 'role__name')
    list_filter = ('role', 'is_active')
    list_per_page = 10

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(IndustryType)


@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display = ("user", "bank_name", "account_number", "account_holder_name", "created_at")
    search_fields = ("bank_name", "account_number", "account_holder_name")


@admin.register(CardDetail)
class CardDetailAdmin(admin.ModelAdmin):
    list_display = ("user", "card_number", "cardholder_name", "expiry_date", "created_at")
    search_fields = ("card_number", "cardholder_name")


@admin.register(PayID)
class PayIDAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "email", "phone_number", "created_at")
    search_fields = ("name", "email", "phone_number")

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'user_agent', 'ip_address', 'expired', 'last_activity')
    list_filter = ('expired', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address', 'user_agent')
    list_per_page = 20
    readonly_fields = ('created_at',)
    
    actions = ['mark_expired', 'mark_active']
    
    def mark_expired(self, request, queryset):
        queryset.update(expired=True)
    mark_expired.short_description = "Mark selected sessions as expired"
    
    def mark_active(self, request, queryset):
        queryset.update(expired=False)
    mark_active.short_description = "Mark selected sessions as active"


@admin.register(CompanySite)
class CompanySiteAdmin(admin.ModelAdmin):
    """Admin for company sites/locations"""
    list_display = ('name', 'company', 'suburb', 'state', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'state', 'country', 'company')
    search_fields = ('name', 'address', 'suburb', 'company__name')
    list_per_page = 20
    ordering = ('company', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('company', 'name', 'is_active')
        }),
        ('Location Details', {
            'fields': ('address', 'suburb', 'state', 'country', 'contact_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')