from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EmailInbox,
    EmailMessage,
    EmailAttachment,
    EmailGuardian,
    SecurityAlert,
    EmailAutomation,
    EmailFolder,
    EmailLabel,
    MessageLabel,
    EmailHistory,
    EmailConfiguration,
    IncomingMailConfiguration,
    EmailTemplate,
    ScheduledEmail,
    EmailGuardianRule,
    EmailScanResult
)
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.safestring import mark_safe
import json

@admin.register(EmailInbox)
class EmailInboxAdmin(admin.ModelAdmin):
    list_display = ('name', 'email_address', 'status_icon', 'message_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email_address')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    def status_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Active</span>')
        return format_html('<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> Inactive</span>')
    status_icon.short_description = 'Status'
    
    def message_count(self, obj):
        count = obj.emailmessage_set.count()
        return format_html('<span class="badge" style="background-color: #17a2b8; color: white;">{}</span>', count)
    message_count.short_description = 'Messages'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active'),
        }),
        ('Email Settings', {
            'fields': ('email_address', 'description'),
        }),
        ('Outgoing Configuration (SMTP)', {
            'fields': ('configuration',),
        }),
        ('Incoming Configuration (IMAP/POP3)', {
            'fields': ('incoming_config',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['activate_inboxes', 'deactivate_inboxes', 'fetch_inbox_emails']
    
    def activate_inboxes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} inbox(es).")
    activate_inboxes.short_description = "Mark selected inboxes as active"
    
    def deactivate_inboxes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} inbox(es).")
    deactivate_inboxes.short_description = "Mark selected inboxes as inactive"
    
    def fetch_inbox_emails(self, request, queryset):
        from .inbox_service import EmailFetchService
        
        total_fetched = 0
        errors = []
        
        for inbox in queryset:
            if not inbox.incoming_config:
                errors.append(f"{inbox.name}: No incoming mail configuration")
                continue
            
            if not inbox.incoming_config.is_active:
                errors.append(f"{inbox.name}: Incoming mail configuration is inactive")
                continue
            
            try:
                service = EmailFetchService(inbox.incoming_config)
                count = service.fetch_emails(inbox)
                total_fetched += count
            except Exception as e:
                errors.append(f"{inbox.name}: {str(e)}")
        
        if total_fetched > 0:
            self.message_user(request, f"Successfully fetched {total_fetched} email(s).", level='success')
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    fetch_inbox_emails.short_description = "Fetch emails from selected inboxes"

@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'from_email', 'inbox', 'status_badge', 'read_status', 'created_at')
    list_filter = ('status', 'is_read', 'inbox', 'created_at')
    search_fields = ('subject', 'from_email', 'body')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'received_at')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def status_badge(self, obj):
        status_colors = {
            'draft': '#6c757d',
            'sent': '#28a745',
            'received': '#17a2b8',
            'failed': '#dc3545',
            'scheduled': '#ffc107',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color: #28a745;"><i class="fas fa-envelope-open"></i> Read</span>')
        return format_html('<span style="color: #ffc107;"><i class="fas fa-envelope"></i> Unread</span>')
    read_status.short_description = 'Read'
    
    fieldsets = (
        ('General', {
            'fields': ('subject', 'inbox'),
        }),
        ('Addressing', {
            'fields': ('from_email', 'to_emails', 'cc_emails', 'bcc_emails'),
        }),
        ('Content', {
            'fields': ('body',),
        }),
        ('HTML Content', {
            'fields': ('html_body',),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status', 'priority'),
        }),
        ('Flags', {
            'fields': ('is_favorite', 'is_read', 'is_replied', 'is_forwarded'),
        }),
        ('Relationships', {
            'fields': ('template', 'parent_message', 'created_by'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'received_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_favorite', 'mark_as_not_favorite']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"Successfully marked {updated} message(s) as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"Successfully marked {updated} message(s) as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"
    
    def mark_as_favorite(self, request, queryset):
        updated = queryset.update(is_favorite=True)
        self.message_user(request, f"Successfully marked {updated} message(s) as favorite.")
    mark_as_favorite.short_description = "Mark selected messages as favorite"
    
    def mark_as_not_favorite(self, request, queryset):
        updated = queryset.update(is_favorite=False)
        self.message_user(request, f"Successfully removed favorite mark from {updated} message(s).")
    mark_as_not_favorite.short_description = "Remove favorite mark from selected messages"

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'get_message_subject', 'file_size', 'file_type', 'created_at')
    list_filter = ('created_at', 'content_type')
    search_fields = ('filename', 'message__subject')
    readonly_fields = ('created_at', 'size')
    
    def file_size(self, obj):
        # Format file size in human-readable format
        size = obj.size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        else:
            return f"{size/(1024*1024):.1f} MB"
    file_size.short_description = 'Size'
    
    def file_type(self, obj):
        content_type = obj.content_type or ''
        icon_class = 'fa-file'
        
        # Assign different icons based on file type
        if 'image' in content_type:
            icon_class = 'fa-file-image'
        elif 'pdf' in content_type:
            icon_class = 'fa-file-pdf'
        elif 'word' in content_type or 'document' in content_type:
            icon_class = 'fa-file-word'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            icon_class = 'fa-file-excel'
        elif 'zip' in content_type or 'compressed' in content_type:
            icon_class = 'fa-file-archive'
        elif 'text' in content_type:
            icon_class = 'fa-file-alt'
            
        return format_html('<i class="fas {} fa-lg"></i> {}', icon_class, content_type)
    file_type.short_description = 'Type'
    
    def get_message_subject(self, obj):
        if obj.message:
            subject = obj.message.subject
            if len(subject) > 30:
                subject = subject[:27] + '...'
            return subject
        return 'N/A'
    get_message_subject.short_description = 'Message Subject'
    
    fieldsets = (
        ('General', {
            'fields': ('filename', 'message'),
        }),
        ('File Details', {
            'fields': ('file', 'size', 'content_type'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

@admin.register(EmailGuardian)
class EmailGuardianAdmin(admin.ModelAdmin):
    list_display = ('name', 'severity_badge', 'status_icon', 'rules_count', 'created_at')
    list_filter = ('severity', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    def severity_badge(self, obj):
        severity_colors = {
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#28a745',
        }
        color = severity_colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.severity.upper()
        )
    severity_badge.short_description = 'Severity'
    
    def status_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;"><i class="fas fa-shield-alt"></i> Active</span>')
        return format_html('<span style="color: #dc3545;"><i class="fas fa-shield-alt"></i> Inactive</span>')
    status_icon.short_description = 'Status'
    
    def rules_count(self, obj):
        count = obj.rules.count() if hasattr(obj, 'rules') else 0
        return format_html('<span class="badge" style="background-color: #17a2b8; color: white;">{}</span>', count)
    rules_count.short_description = 'Rules'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active'),
        }),
        ('Guardian Details', {
            'fields': ('description', 'severity'),
        }),
        ('Configuration', {
            'fields': ('rules',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['activate_guardians', 'deactivate_guardians']
    
    def activate_guardians(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} guardian(s).")
    activate_guardians.short_description = "Activate selected guardians"
    
    def deactivate_guardians(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} guardian(s).")
    deactivate_guardians.short_description = "Deactivate selected guardians"

@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type_badge', 'get_guardian_name', 'get_message_subject', 'resolution_status', 'created_at')
    list_filter = ('alert_type', 'is_resolved', 'created_at')
    search_fields = ('description', 'message__subject')
    readonly_fields = ('created_at', 'resolved_at')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def alert_type_badge(self, obj):
        alert_colors = {
            'phishing': '#dc3545',
            'spam': '#ffc107',
            'malware': '#dc3545',
            'sensitive_data': '#6610f2',
            'suspicious': '#17a2b8',
            'other': '#6c757d',
        }
        color = alert_colors.get(obj.alert_type, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.alert_type.upper()
        )
    alert_type_badge.short_description = 'Alert Type'
    
    def resolution_status(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Resolved</span>')
        return format_html('<span style="color: #dc3545;"><i class="fas fa-exclamation-circle"></i> Unresolved</span>')
    resolution_status.short_description = 'Status'
    
    def get_guardian_name(self, obj):
        return obj.guardian.name if obj.guardian else 'N/A'
    get_guardian_name.short_description = 'Guardian'
    
    def get_message_subject(self, obj):
        if obj.message:
            subject = obj.message.subject
            if len(subject) > 30:
                subject = subject[:27] + '...'
            return subject
        return 'N/A'
    get_message_subject.short_description = 'Message'
    
    fieldsets = (
        ('General', {
            'fields': ('alert_type', 'guardian', 'message'),
        }),
        ('Alert Details', {
            'fields': ('description', 'is_resolved'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'resolved_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_unresolved']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f"Successfully marked {updated} alert(s) as resolved.")
    mark_as_resolved.short_description = "Mark selected alerts as resolved"
    
    def mark_as_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_at=None)
        self.message_user(request, f"Successfully marked {updated} alert(s) as unresolved.")
    mark_as_unresolved.short_description = "Mark selected alerts as unresolved"

@admin.register(EmailAutomation)
class EmailAutomationAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_badge', 'action_badge', 'status_icon', 'created_at')
    list_filter = ('trigger_type', 'action_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    def trigger_badge(self, obj):
        trigger_colors = {
            'message_received': '#17a2b8',
            'message_sent': '#28a745',
            'scheduled': '#ffc107',
            'manual': '#6c757d',
            'condition_met': '#6610f2',
        }
        color = trigger_colors.get(obj.trigger_type, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.get_trigger_type_display()
        )
    trigger_badge.short_description = 'Trigger'
    
    def action_badge(self, obj):
        action_colors = {
            'send_email': '#007bff',
            'tag_message': '#20c997',
            'move_to_folder': '#fd7e14',
            'delete_message': '#dc3545',
            'forward_message': '#6610f2',
        }
        color = action_colors.get(obj.action_type, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.get_action_type_display()
        )
    action_badge.short_description = 'Action'
    
    def status_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Active</span>')
        return format_html('<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> Inactive</span>')
    status_icon.short_description = 'Status'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active'),
        }),
        ('Automation Details', {
            'fields': ('description', 'trigger_type', 'action_type'),
        }),
        ('Configuration', {
            'fields': ('conditions', 'actions'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['activate_automations', 'deactivate_automations']
    
    def activate_automations(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} automation(s).")
    activate_automations.short_description = "Activate selected automations"
    
    def deactivate_automations(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} automation(s).")
    deactivate_automations.short_description = "Deactivate selected automations"

@admin.register(EmailFolder)
class EmailFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_folder_display', 'message_count', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    def parent_folder_display(self, obj):
        if obj.parent_folder:
            return obj.parent_folder.name
        return format_html('<span style="color: #6c757d;">Root</span>')
    parent_folder_display.short_description = 'Parent Folder'
    
    def message_count(self, obj):
        # This requires a custom count method or query
        # For now, we'll just show a placeholder
        return format_html('<span class="badge" style="background-color: #17a2b8; color: white;">0</span>')
    message_count.short_description = 'Messages'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'parent_folder'),
        }),
        ('Folder Details', {
            'fields': ('description', 'created_by'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

@admin.register(EmailLabel)
class EmailLabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_swatch', 'message_count', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    
    def color_swatch(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border-radius: 4px; margin-right: 5px;"></span> {}',
            obj.color, obj.color
        )
    color_swatch.short_description = 'Color'
    
    def message_count(self, obj):
        count = MessageLabel.objects.filter(label=obj).count()
        return format_html('<span class="badge" style="background-color: #17a2b8; color: white;">{}</span>', count)
    message_count.short_description = 'Messages'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'color'),
        }),
        ('Label Details', {
            'fields': ('description', 'created_by'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

@admin.register(MessageLabel)
class MessageLabelAdmin(admin.ModelAdmin):
    list_display = ('get_message_subject', 'get_label_name', 'get_label_color', 'created_at')
    list_filter = ('created_at', 'label')
    search_fields = ('message__subject', 'label__name')
    readonly_fields = ('created_at',)
    
    def get_message_subject(self, obj):
        if obj.message:
            subject = obj.message.subject
            if len(subject) > 30:
                subject = subject[:27] + '...'
            return subject
        return 'N/A'
    get_message_subject.short_description = 'Message'
    
    def get_label_name(self, obj):
        return obj.label.name if obj.label else 'N/A'
    get_label_name.short_description = 'Label'
    
    def get_label_color(self, obj):
        if obj.label and obj.label.color:
            return format_html(
                '<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border-radius: 4px;"></span>',
                obj.label.color
            )
        return 'N/A'
    get_label_color.short_description = 'Color'
    
    fieldsets = (
        ('General', {
            'fields': ('message', 'label'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

@admin.register(EmailHistory)
class EmailHistoryAdmin(admin.ModelAdmin):
    list_display = ('colored_email_type', 'recipient_email', 'subject_preview', 'status_badge', 'sent_at', 'get_error_preview')
    list_filter = ('email_type', 'status', 'sent_at')
    search_fields = ('recipient_email', 'subject', 'body', 'error_message')
    readonly_fields = ('sent_at', 'error_message')
    list_per_page = 25
    ordering = ('-sent_at',)
    date_hierarchy = 'sent_at'
    actions = ['retry_failed_emails']
    
    def colored_email_type(self, obj):
        email_type_colors = {
            'contact_form': '#007bff',
            'appointment_request': '#28a745',
            'appointment_confirmation': '#17a2b8', 
            'appointment_reminder': '#6610f2',
            'appointment_cancellation': '#dc3545',
            'test_email': '#fd7e14',
            'newsletter': '#20c997',
            'scheduled_email': '#6f42c1',
            'other': '#6c757d',
        }
        color = email_type_colors.get(obj.email_type, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.get_email_type_display()
        )
    colored_email_type.short_description = 'Email Type'
    
    def subject_preview(self, obj):
        subject = obj.subject or ''
        if len(subject) > 30:
            subject = subject[:27] + '...'
        return subject
    subject_preview.short_description = 'Subject'
    
    def status_badge(self, obj):
        if obj.status == 'success':
            color = '#28a745'
        elif obj.status == 'failed':
            color = '#dc3545'
        else:
            color = '#6c757d'
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def get_error_preview(self, obj):
        if obj.error_message and obj.status == 'failed':
            error = obj.error_message
            if len(error) > 50:
                error = error[:47] + '...'
            return format_html('<span style="color: #dc3545; font-size: 12px;">{}</span>', error)
        return '-'
    get_error_preview.short_description = 'Error'
    
    fieldsets = (
        ('General', {
            'fields': ('email_type', 'status'),
        }),
        ('Recipient', {
            'fields': ('recipient_email', 'subject'),
        }),
        ('Content', {
            'fields': ('body',),
        }),
        ('HTML Content', {
            'fields': ('html_body',),
            'classes': ('collapse',),
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Related Objects', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('sent_at',),
            'classes': ('collapse',),
        }),
    )

    def retry_failed_emails(self, request, queryset):
        success_count = 0
        error_count = 0
        for email in queryset:
            if email.status == 'failed':
                try:
                    # Use Django's send_mail function for simple retry
                    send_mail(
                        email.subject,
                        email.body,
                        from_email=None,  # Use default from email
                        recipient_list=[email.recipient_email],
                        html_message=email.html_body
                    )
                    email.status = 'success'
                    email.error_message = ''
                    email.save()
                    success_count += 1
                except Exception as e:
                    # Keep failed status and update error message
                    email.error_message = str(e)
                    email.save()
                    error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully resent {success_count} email(s).", level='success')
        if error_count > 0:
            self.message_user(request, f"Failed to resend {error_count} email(s).", level='error')
    retry_failed_emails.short_description = "Retry sending failed emails"

@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email_host', 'email_host_user', 'is_default', 'test_buttons')
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
    
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css',
            )
        }
        js = ('https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js',)

    def test_buttons(self, obj):
        """
        Render a button to test the email configuration
        """
        if obj.id:
            # Get all templates for the dropdown
            templates = EmailTemplate.objects.all()
            template_options = ''.join([f'<option value="{t.id}">{t.name}</option>' for t in templates])
            
            button_html = f'''
            <button type="button" class="test-email-btn" 
                onclick="openEmailTestModal{obj.id}()" 
                style="background-color: #6200ee; color: white; border: none; padding: 5px 15px; 
                       border-radius: 4px; cursor: pointer;">
                <i class="fas fa-paper-plane"></i> Test Email
            </button>
            
            <div id="emailTestModal{obj.id}" class="email-test-modal" style="display:none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1000; background-color: rgba(0,0,0,0.5);">
                <div class="email-test-modal-content" style="position: relative; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); max-width: 500px; width: 100%;">
                    <h3 style="margin-top: 0; margin-bottom: 15px; color: #6200ee;">Test Email Configuration</h3>
                    <p style="margin-bottom: 20px;">Send a test email using this configuration:</p>
                    <div style="margin-bottom: 15px;">
                        <label for="recipientEmail{obj.id}" style="display: block; margin-bottom: 5px; font-weight: bold;">Recipient Email:</label>
                        <input type="email" id="recipientEmail{obj.id}" placeholder="Enter email address" 
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label for="templateSelect{obj.id}" style="display: block; margin-bottom: 5px; font-weight: bold;">Email Template:</label>
                        <select id="templateSelect{obj.id}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="">-- Select Template (Optional) --</option>
                            {template_options}
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: flex; align-items: center;">
                            <input type="checkbox" id="setAsDefault{obj.id}" style="margin-right: 8px;">
                            Set selected template as default for this configuration
                        </label>
                    </div>
                    <div style="text-align: right; margin-top: 20px;">
                        <button type="button" onclick="closeEmailModal{obj.id}()" 
                                style="background-color: #f5f5f5; color: #333; border: 1px solid #ddd; padding: 8px 15px; 
                                       border-radius: 4px; margin-right: 10px; cursor: pointer;">
                            Cancel
                        </button>
                        <button type="button" onclick="sendTestEmail{obj.id}()" 
                                style="background-color: #6200ee; color: white; border: none; padding: 8px 15px; 
                                       border-radius: 4px; cursor: pointer;">
                            Send Test Email
                        </button>
                    </div>
                </div>
            </div>
            '''
            
            # Add unique JS functions for this configuration
            js = f'''
            <script>
            // Create unique functions for config ID {obj.id}
            function openEmailTestModal{obj.id}() {{
                document.getElementById('emailTestModal{obj.id}').style.display = 'block';
                document.body.style.overflow = 'hidden';
            }}
            
            function closeEmailModal{obj.id}() {{
                document.getElementById('emailTestModal{obj.id}').style.display = 'none';
                document.body.style.overflow = '';
            }}
            
            function sendTestEmail{obj.id}() {{
                // Ensure SweetAlert is loaded
                if (typeof Swal === 'undefined') {{
                    var sweetAlertScript = document.createElement('script');
                    sweetAlertScript.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11';
                    sweetAlertScript.async = true;
                    document.head.appendChild(sweetAlertScript);
                    setTimeout(sendTestEmail{obj.id}, 500);
                    return;
                }}
                
                const recipientEmail = document.getElementById('recipientEmail{obj.id}').value;
                const templateId = document.getElementById('templateSelect{obj.id}').value;
                const setAsDefault = document.getElementById('setAsDefault{obj.id}').checked;
                
                if (!recipientEmail) {{
                    Swal.fire({{
                        title: 'Error',
                        text: 'Please enter a recipient email address',
                        icon: 'error'
                    }});
                    return;
                }}
                
                // Show loading indicator
                Swal.fire({{
                    title: 'Sending Test Email',
                    html: 'Please wait...',
                    allowOutsideClick: false,
                    didOpen: () => {{
                        Swal.showLoading();
                    }}
                }});
                
                // Get CSRF token
                function getCookie(name) {{
                    let cookieValue = null;
                    if (document.cookie && document.cookie !== '') {{
                        const cookies = document.cookie.split(';');
                        for (let i = 0; i < cookies.length; i++) {{
                            const cookie = cookies[i].trim();
                            if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }}
                        }}
                    }}
                    return cookieValue;
                }}
                
                const csrftoken = getCookie('csrftoken');
                
                // Prepare data
                const data = JSON.stringify({{
                    email: recipientEmail,
                    template_id: templateId || null,
                    set_as_default: setAsDefault
                }});
                
                // Send request
                fetch('/email/test-email-config/{obj.id}/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    }},
                    body: data
                }})
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error('Network response was not ok: ' + response.status);
                    }}
                    return response.json();
                }})
                .then(data => {{
                    closeEmailModal{obj.id}();
                    
                    if (data.status === 'success') {{
                        Swal.fire({{
                            title: 'Success',
                            text: data.message,
                            icon: 'success'
                        }});
                    }} else {{
                        Swal.fire({{
                            title: 'Error',
                            text: data.message,
                            icon: 'error'
                        }});
                    }}
                }})
                .catch(error => {{
                    closeEmailModal{obj.id}();
                    console.error('Error:', error);
                    Swal.fire({{
                        title: 'Error',
                        text: 'Failed to send test email: ' + error.message,
                        icon: 'error'
                    }});
                }});
            }}
            
            // Ensure Font Awesome is loaded
            if (!document.querySelector('link[href*="fontawesome"]')) {{
                var fontAwesomeLink = document.createElement('link');
                fontAwesomeLink.rel = 'stylesheet';
                fontAwesomeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
                document.head.appendChild(fontAwesomeLink);
            }}
            
            // Close modal if clicked outside of content
            document.addEventListener('click', function(event) {{
                if (event.target === document.getElementById('emailTestModal{obj.id}')) {{
                    closeEmailModal{obj.id}();
                }}
            }});
            </script>
            '''
            
            return mark_safe(button_html + js)
        return ""

    test_buttons.short_description = "Actions"

    def test_email_configuration(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one configuration to test.", level='warning')
            return
            
        config = queryset.first()
        try:
            from django.core.mail.backends.smtp import EmailBackend
            from django.core.mail import EmailMessage
            
            # Get recipient email
            recipient = config.test_email or config.email_host_user
            
            # Set up the connection
            connection = EmailBackend(
                host=config.email_host,
                port=config.email_port,
                username=config.email_host_user,
                password=config.email_host_password,
                use_tls=config.email_use_tls,
                use_ssl=config.email_use_ssl,
                fail_silently=False,
            )
            
            # Create the email
            email = EmailMessage(
                subject=f'Test Email from {config.name}',
                body=f'This is a test email sent from the MyComparables email system using the {config.name} configuration at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}.',
                from_email=config.default_from_email,
                to=[recipient],
                connection=connection,
            )
            
            # Send the email
            email.send()
            
            self.message_user(request, f"Test email sent successfully to {recipient}.", level='success')
        except Exception as e:
            self.message_user(request, f"Error testing email configuration: {str(e)}", level='error')
            
    test_email_configuration.short_description = "Send test email"
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override to add custom JavaScript for the test email button"""
        extra_context = extra_context or {}
        extra_context['test_email_url'] = request.path
        return super().change_view(request, object_id, form_url, extra_context)
    
    def changelist_view(self, request, extra_context=None):
        """Override to add JavaScript for the test email button in the list view"""
        extra_context = extra_context or {}
        extra_context['has_sweetalert'] = True
        return super().changelist_view(request, extra_context)

@admin.register(IncomingMailConfiguration)
class IncomingMailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email_address', 'protocol_badge', 'security_badge', 'status_icon', 'last_fetched')
    list_filter = ('protocol', 'connection_security', 'is_active', 'created_at')
    search_fields = ('name', 'email_address', 'mail_server', 'username')
    readonly_fields = ('created_at', 'updated_at', 'last_fetched')
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active'),
        }),
        ('Email Account', {
            'fields': ('email_address', 'protocol'),
        }),
        ('Server Settings', {
            'fields': ('mail_server', 'mail_port', 'connection_security'),
        }),
        ('Authentication', {
            'fields': ('username', 'password', 'auth_method'),
        }),
        ('Fetch Settings', {
            'fields': ('auto_fetch', 'fetch_interval', 'fetch_on_startup'),
        }),
        ('Folder Settings', {
            'fields': ('inbox_folder', 'trash_folder'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_fetched'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['test_connection_action', 'fetch_emails_action']
    
    def protocol_badge(self, obj):
        protocol_colors = {
            'imap': '#007bff',
            'pop3': '#28a745',
        }
        color = protocol_colors.get(obj.protocol, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.protocol.upper()
        )
    protocol_badge.short_description = 'Protocol'
    
    def security_badge(self, obj):
        security_colors = {
            'ssl': '#28a745',
            'starttls': '#17a2b8',
            'none': '#dc3545',
        }
        color = security_colors.get(obj.connection_security, '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            color, obj.connection_security.upper()
        )
    security_badge.short_description = 'Security'
    
    def status_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Active</span>')
        return format_html('<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> Inactive</span>')
    status_icon.short_description = 'Status'
    
    def test_connection_action(self, request, queryset):
        from .inbox_service import EmailFetchService
        
        success_count = 0
        error_count = 0
        
        for config in queryset:
            try:
                service = EmailFetchService(config)
                service.connect()
                service.disconnect()
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(request, f"{config.name}: {str(e)}", level='error')
        
        if success_count > 0:
            self.message_user(request, f"Successfully connected to {success_count} server(s).", level='success')
    
    test_connection_action.short_description = "Test connection to selected servers"
    
    def fetch_emails_action(self, request, queryset):
        from .inbox_service import EmailFetchService
        
        total_fetched = 0
        errors = []
        
        for config in queryset:
            if not config.is_active:
                continue
            
            # Get all inboxes using this config
            inboxes = EmailInbox.objects.filter(incoming_config=config, is_active=True)
            
            for inbox in inboxes:
                try:
                    service = EmailFetchService(config)
                    count = service.fetch_emails(inbox)
                    total_fetched += count
                except Exception as e:
                    errors.append(f"{inbox.name}: {str(e)}")
        
        if total_fetched > 0:
            self.message_user(request, f"Successfully fetched {total_fetched} email(s).", level='success')
        
        if errors:
            self.message_user(request, "Errors: " + "; ".join(errors), level='error')
    
    fetch_emails_action.short_description = "Fetch emails for selected configurations"

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
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
            # Create a new template with the same data
            new_template = template
            new_template.pk = None  # This makes it a new object
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

@admin.register(ScheduledEmail)
class ScheduledEmailAdmin(admin.ModelAdmin):
    list_display = ('template', 'subject_preview', 'scheduled_time', 'status_badge', 'attempts', 'created_at')
    list_filter = ('status', 'scheduled_time', 'created_at', 'attempts')
    search_fields = ('template__name', 'subject_override', 'error_message')
    readonly_fields = ('created_at', 'sent_time', 'last_attempt', 'attempts', 'error_message')
    list_per_page = 25
    date_hierarchy = 'scheduled_time'
    
    def subject_preview(self, obj):
        subject = obj.subject_override or (obj.template.subject if obj.template else '')
        if subject:
            if len(subject) > 40:
                return subject[:40] + '...'
            return subject
        return '-'
    subject_preview.short_description = 'Subject'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'sent': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    fieldsets = (
        ('General', {
            'fields': ('template', 'status'),
        }),
        ('Schedule', {
            'fields': ('scheduled_time', 'recipients'),
        }),
        ('Content Overrides', {
            'fields': ('subject_override', 'variables_data'),
        }),
        ('Delivery Status', {
            'fields': ('attempts', 'sent_time', 'last_attempt', 'error_message'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_as_pending', 'mark_as_cancelled', 'reschedule_for_today', 'reset_attempts']
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, f"Successfully marked {queryset.count()} email(s) as pending.")
    mark_as_pending.short_description = "Mark selected emails as pending"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"Successfully cancelled {queryset.count()} email(s).")
    mark_as_cancelled.short_description = "Mark selected emails as cancelled"
    
    def reschedule_for_today(self, request, queryset):
        queryset.update(scheduled_time=timezone.now(), status='pending')
        self.message_user(request, f"Successfully rescheduled {queryset.count()} email(s) for now.")
    reschedule_for_today.short_description = "Reschedule selected emails for now"
    
    def reset_attempts(self, request, queryset):
        queryset.update(attempts=0, status='pending')
        self.message_user(request, f"Successfully reset attempts for {queryset.count()} email(s).")
    reset_attempts.short_description = "Reset attempts counter"

@admin.register(EmailGuardianRule)
class EmailGuardianRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_guardian', 'get_action', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'pattern')
    readonly_fields = ('created_at',)
    
    def get_guardian(self, obj):
        return obj.guardian.name if hasattr(obj, 'guardian') else 'N/A'
    get_guardian.short_description = 'Guardian'
    
    def get_action(self, obj):
        return obj.action if hasattr(obj, 'action') else 'N/A'
    get_action.short_description = 'Action'
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active'),
        }),
        ('Rule Details', {
            'fields': ('description',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

@admin.register(EmailScanResult)
class EmailScanResultAdmin(admin.ModelAdmin):
    list_display = ('get_email_subject', 'get_rule_name', 'scan_date', 'action_taken')
    list_filter = ('action_taken', 'scan_date')
    search_fields = ('email__subject', 'guardian_rule__name', 'matched_content')
    list_per_page = 25
    date_hierarchy = 'scan_date'
    
    def get_email_subject(self, obj):
        if hasattr(obj, 'email') and obj.email:
            return obj.email.subject
        return 'N/A'
    get_email_subject.short_description = 'Email Subject'
    
    def get_rule_name(self, obj):
        if hasattr(obj, 'guardian_rule') and obj.guardian_rule:
            return obj.guardian_rule.name
        return 'N/A'
    get_rule_name.short_description = 'Guardian Rule'
    
    fieldsets = (
        ('Scan Details', {
            'fields': ('email', 'guardian_rule', 'action_taken'),
        }),
        ('Match Details', {
            'fields': ('matched_content', 'details'),
        }),
    )
    
    actions = ['mark_as_delete', 'mark_as_notify']
    
    def mark_as_delete(self, request, queryset):
        queryset.update(action_taken='delete')
    mark_as_delete.short_description = "Mark selected results for deletion"
    
    def mark_as_notify(self, request, queryset):
        queryset.update(action_taken='notify')
    mark_as_notify.short_description = "Mark selected results for notification"

