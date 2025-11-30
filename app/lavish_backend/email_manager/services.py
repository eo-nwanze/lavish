import re
from django.conf import settings
from .models import EmailGuardianRule, EmailScanResult, EmailMessage
from django.utils import timezone

class EmailGuardianService:
    def __init__(self):
        self.rules = EmailGuardianRule.objects.filter(is_active=True)
        
    def scan_email(self, email_message):
        """
        Scan an email message against all active guardian rules
        Returns a list of scan results
        """
        scan_results = []
        
        for rule in self.rules:
            # Check subject
            subject_match = re.search(rule.pattern, email_message.subject, re.IGNORECASE)
            if subject_match:
                result = self._create_scan_result(email_message, rule, subject_match.group(0))
                scan_results.append(result)
                continue
                
            # Check body
            body_match = re.search(rule.pattern, email_message.body, re.IGNORECASE)
            if body_match:
                result = self._create_scan_result(email_message, rule, body_match.group(0))
                scan_results.append(result)
                continue
                
            # Check attachments
            for attachment in email_message.attachments.all():
                if attachment.file:
                    # For text files, check content
                    if attachment.file.name.endswith(('.txt', '.html', '.htm')):
                        content = attachment.file.read().decode('utf-8', errors='ignore')
                        content_match = re.search(rule.pattern, content, re.IGNORECASE)
                        if content_match:
                            result = self._create_scan_result(
                                email_message, 
                                rule, 
                                content_match.group(0),
                                attachment=attachment
                            )
                            scan_results.append(result)
                            break
                    else:
                        # For binary files, check filename
                        filename_match = re.search(rule.pattern, attachment.file.name, re.IGNORECASE)
                        if filename_match:
                            result = self._create_scan_result(
                                email_message, 
                                rule, 
                                attachment.file.name,
                                attachment=attachment
                            )
                            scan_results.append(result)
                            break
        
        return scan_results
    
    def _create_scan_result(self, email_message, rule, matched_content, attachment=None):
        """
        Create a scan result record and take appropriate action
        """
        # Create scan result
        result = EmailScanResult.objects.create(
            email=email_message,
            guardian_rule=rule,
            matched_content=matched_content,
            action_taken=rule.action,
            details={
                'attachment': attachment.file.name if attachment else None,
                'severity': rule.severity,
                'pattern': rule.pattern
            }
        )
        
        # Take action based on rule
        if rule.action == 'quarantine':
            email_message.is_quarantined = True
            email_message.save()
        elif rule.action == 'delete':
            email_message.delete()
        elif rule.action == 'mark_spam':
            email_message.is_spam = True
            email_message.save()
        elif rule.action == 'notify':
            self._notify_admin(email_message, rule, matched_content)
        
        return result
    
    def _notify_admin(self, email_message, rule, matched_content):
        """
        Send notification to admin about suspicious email
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f'[Email Guardian Alert] Suspicious Email Detected - {rule.severity.upper()}'
        message = f"""
        A suspicious email has been detected by the Email Guardian system.
        
        Details:
        - Rule: {rule.name}
        - Severity: {rule.severity}
        - From: {email_message.from_email}
        - Subject: {email_message.subject}
        - Matched Content: {matched_content}
        
        Please review this email and take appropriate action.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )

class DeviceManagementService:
    def __init__(self):
        self.devices = Device.objects.all()
    
    def execute_script(self, device, script):
        """
        Execute a script on a device
        """
        execution = DeviceScriptExecution.objects.create(
            device=device,
            script=script,
            status='pending'
        )
        
        try:
            # Here you would implement the actual script execution logic
            # This could involve:
            # 1. Connecting to the device via SSH or other protocol
            # 2. Transferring the script
            # 3. Executing the script
            # 4. Capturing output
            
            # For now, we'll simulate execution
            import time
            time.sleep(2)  # Simulate script execution
            
            execution.complete(output="Script executed successfully")
            
        except Exception as e:
            execution.complete(error=str(e))
    
    def update_security_score(self, device):
        """
        Update device security score based on various factors
        """
        score = 100  # Start with perfect score
        
        # Check for outdated scripts
        outdated_scripts = DeviceScriptExecution.objects.filter(
            device=device,
            status='completed',
            completion_date__lt=timezone.now() - timezone.timedelta(days=30)
        )
        score -= outdated_scripts.count() * 5
        
        # Check for failed script executions
        failed_scripts = DeviceScriptExecution.objects.filter(
            device=device,
            status='failed'
        )
        score -= failed_scripts.count() * 10
        
        # Check for inactive status
        if device.status != 'active':
            score -= 20
        
        # Ensure score stays within bounds
        score = max(0, min(100, score))
        
        device.security_score = score
        device.save()
        
        return score 