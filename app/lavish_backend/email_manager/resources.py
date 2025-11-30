from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateWidget, DateTimeWidget
from email_manager.models import (
    EmailConfiguration, EmailTemplate, EmailHistory, 
    EmailInbox, EmailMessage, EmailAttachment, EmailFolder, EmailLabel
)
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser

class EmailConfigurationResource(resources.ModelResource):
    class Meta:
        model = EmailConfiguration
        fields = ('id', 'name', 'email_host', 'email_port', 'email_host_user', 'email_use_tls', 
                  'email_use_ssl', 'default_from_email', 'is_default', 'created_at', 'updated_at')
        export_order = fields
        import_id_fields = ('id',)
        # Don't export sensitive information
        exclude = ('email_host_password',)

class EmailTemplateResource(resources.ModelResource):
    configuration = fields.Field(
        column_name='configuration',
        attribute='configuration',
        widget=ForeignKeyWidget(EmailConfiguration, field='name')
    )
    created_at = fields.Field(
        column_name='created_at',
        attribute='created_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )
    updated_at = fields.Field(
        column_name='updated_at',
        attribute='updated_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )

    class Meta:
        model = EmailTemplate
        fields = ('id', 'name', 'description', 'subject', 'configuration', 
                  'template_type', 'is_active', 'created_at', 'updated_at')
        export_order = fields
        import_id_fields = ('id',)
        # Don't export the actual template content as it might be large
        exclude = ('html_content', 'text_content')

class EmailHistoryResource(resources.ModelResource):
    sent_at = fields.Field(
        column_name='sent_at',
        attribute='sent_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )

    class Meta:
        model = EmailHistory
        fields = ('id', 'email_type', 'recipient_email', 'subject', 'status', 
                  'sent_at', 'error_message')
        export_order = fields
        import_id_fields = ('id',)
        # Don't export the body content as it might be large
        exclude = ('body', 'html_body')

class EmailInboxResource(resources.ModelResource):
    configuration = fields.Field(
        column_name='configuration',
        attribute='configuration',
        widget=ForeignKeyWidget(EmailConfiguration, field='name')
    )
    created_at = fields.Field(
        column_name='created_at',
        attribute='created_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )
    updated_at = fields.Field(
        column_name='updated_at',
        attribute='updated_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )

    class Meta:
        model = EmailInbox
        fields = ('id', 'name', 'email_address', 'configuration', 
                  'is_active', 'created_at', 'updated_at')
        export_order = fields
        import_id_fields = ('id',)

class EmailFolderResource(resources.ModelResource):
    parent_folder = fields.Field(
        column_name='parent_folder',
        attribute='parent_folder',
        widget=ForeignKeyWidget(EmailFolder, field='name')
    )
    created_by = fields.Field(
        column_name='created_by',
        attribute='created_by',
        widget=ForeignKeyWidget(CustomUser, field='username')
    )
    created_at = fields.Field(
        column_name='created_at',
        attribute='created_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )

    class Meta:
        model = EmailFolder
        fields = ('id', 'name', 'description', 'parent_folder', 'created_by', 'created_at')
        export_order = fields
        import_id_fields = ('id',)

class EmailLabelResource(resources.ModelResource):
    created_by = fields.Field(
        column_name='created_by',
        attribute='created_by',
        widget=ForeignKeyWidget(CustomUser, field='username')
    )
    created_at = fields.Field(
        column_name='created_at',
        attribute='created_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )

    class Meta:
        model = EmailLabel
        fields = ('id', 'name', 'color', 'created_by', 'created_at')
        export_order = fields
        import_id_fields = ('id',) 