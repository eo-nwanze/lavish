"""
Email Manager Admin - Simplified Version
=========================================

This is a simplified version that only shows:
- Email Configuration
- Email Template

All other models are hidden from admin to reduce clutter.

To restore other models, see the full admin.py.backup file.
"""

from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import EmailConfiguration, EmailTemplate
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.safestring import mark_safe


# ============================================================================
# VISIBLE ADMIN MODELS
# ============================================================================

class EmailConfigurationResource(resources.ModelResource):
    class Meta:
        model = EmailConfiguration
        import_id_fields = ['id']
        exclude = ('email_host_password',)


class EmailTemplateResource(resources.ModelResource):
    class Meta:
        model = EmailTemplate
        import_id_fields = ['id']


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(ImportExportModelAdmin):
    resource_class = EmailConfigurationResource
    list_display = ('name', 'email_host', 'email_host_user', 'is_default')
    list_filter = ('is_default', 'email_use_tls', 'email_use_ssl', 'created_at')
    search_fields = ('name', 'email_host', 'email_host_user')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_default', 'test_email'),
        }),
        ('Server Settings', {
            'fields': ('email_host', 'email_port'),
        }),
        ('Authentication', {
            'fields': ('email_host_user', 'email_host_password'),
        }),
        ('Security', {
            'fields': ('email_use_tls', 'email_use_ssl'),
        }),
        ('Email Settings', {
            'fields': ('default_from_email',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(ImportExportModelAdmin):
    resource_class = EmailTemplateResource
    list_display = ('name', 'template_type_badge', 'is_active_icon', 'created_at', 'updated_at')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'html_content', 'plain_text_content')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    ordering = ('-updated_at',)
    
    def template_type_badge(self, obj):
        template_type_colors = {
            'contact_form': '#007bff',
            'appointment_request': '#28a745',
            'appointment_confirmation': '#17a2b8', 
            'appointment_reminder': '#6610f2',
            'appointment_cancellation': '#dc3545',
            'newsletter': '#20c997',
            'welcome': '#fd7e14',
            'custom': '#6c757d',
        }
        color = template_type_colors.get(obj.template_type, '#6c757d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_template_type_display()
        )
    template_type_badge.short_description = 'Template Type'
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Active</span>')
        return format_html('<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> Inactive</span>')
    is_active_icon.short_description = 'Status'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active'),
        }),
        ('Template Details', {
            'fields': ('template_type', 'subject'),
        }),
        ('HTML Content', {
            'fields': ('html_content',),
        }),
        ('Plain Text', {
            'fields': ('plain_text_content',),
        }),
        ('Configuration', {
            'fields': ('configuration', 'variables'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['duplicate_template', 'activate_templates', 'deactivate_templates']
    
    def duplicate_template(self, request, queryset):
        for template in queryset:
            new_template = template
            new_template.pk = None
            new_template.name = f"Copy of {template.name}"
            new_template.save()
        self.message_user(request, f"Successfully duplicated {queryset.count()} template(s).")
    duplicate_template.short_description = "Duplicate selected templates"
    
    def activate_templates(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} template(s).")
    activate_templates.short_description = "Activate selected templates"
    
    def deactivate_templates(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} template(s).")
    deactivate_templates.short_description = "Deactivate selected templates"

