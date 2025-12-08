"""
Script to hide email_manager models from Django admin

This will comment out the admin registrations for:
- Email Attachments
- Email Automations
- Email Folders
- Email Guardians
- Email History
- Email Inboxes
- Email Labels
- Email Messages
- Email guardian rules
- Email scan results
- Incoming Mail Configs
- Message Labels
- Scheduled Emails
- Security Alerts
"""

import os

# Read the admin.py file
admin_file_path = os.path.join(os.path.dirname(__file__), 'email_manager', 'admin.py')

with open(admin_file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# List of admin classes to hide
models_to_hide = [
    'EmailInboxAdmin',
    'EmailMessageAdmin',
    'EmailAttachmentAdmin',
    'EmailGuardianAdmin',
    'SecurityAlertAdmin',
    'EmailAutomationAdmin',
    'EmailFolderAdmin',
    'EmailLabelAdmin',
    'MessageLabelAdmin',
    'EmailHistoryAdmin',
    'IncomingMailConfigurationAdmin',
    'ScheduledEmailAdmin',
    'EmailGuardianRuleAdmin',
    'EmailScanResultAdmin'
]

# Keep these visible
models_to_keep = [
    'EmailConfigurationAdmin',
    'EmailTemplateAdmin'
]

# Add comments at the beginning explaining what's hidden
header_comment = """
# ==================================================================================
# HIDDEN ADMIN MODELS (User Request - Dec 6, 2025)
# ==================================================================================
# The following models are commented out to reduce admin clutter:
# - Email Attachments, Email Automations, Email Folders, Email Guardians
# - Email History, Email Inboxes, Email Labels, Email Messages
# - Email Guardian Rules, Email Scan Results, Incoming Mail Configs
# - Message Labels, Scheduled Emails, Security Alerts
#
# To show these models again, uncomment their @admin.register decorators and class definitions
# Only EmailConfiguration and EmailTemplate remain visible
# ==================================================================================

"""

# Find all @admin.register decorators and comment them out
lines = content.split('\n')
new_lines = []
in_hidden_class = False
hidden_class_name = None
decorator_count = 0

for i, line in enumerate(lines):
    # Check if this is a decorator for a class we want to hide
    if '@admin.register(' in line:
        # Look ahead to find the class name
        for j in range(i+1, min(i+5, len(lines))):
            if 'class ' in lines[j]:
                class_name = lines[j].split('class ')[1].split('(')[0].strip()
                if class_name in models_to_hide:
                    in_hidden_class = True
                    hidden_class_name = class_name
                    new_lines.append('# ' + line)  # Comment out the decorator
                    decorator_count += 1
                    break
                else:
                    new_lines.append(line)
                    break
        else:
            new_lines.append(line)
    elif in_hidden_class:
        # Check if we're still in the class definition
        if line.strip() and not line.startswith(' ') and not line.startswith('#'):
            # We've exited the class
            in_hidden_class = False
            hidden_class_name = None
            new_lines.append(line)
        else:
            # Still in the class, comment it out
            if line.strip():  # Don't add # to empty lines
                new_lines.append('# ' + line)
            else:
                new_lines.append(line)
    else:
        new_lines.append(line)

# Join back together
new_content = header_comment + '\n'.join(new_lines)

# Write back to file
with open(admin_file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Hidden {decorator_count} admin models from email_manager")
print(f"   File: {admin_file_path}")
print(f"\nModels hidden:")
for model in models_to_hide:
    print(f"   - {model}")
print(f"\nModels still visible:")
for model in models_to_keep:
    print(f"   - {model}")




