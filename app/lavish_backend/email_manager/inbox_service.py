"""
Service for handling IMAP/POP3 email fetching and inbox management
"""
import imaplib
import poplib
import email
from email.header import decode_header
from email.utils import parseaddr
import logging
from django.utils import timezone
from .models import IncomingMailConfiguration, EmailInbox, EmailMessage, EmailAttachment
from django.core.files.base import ContentFile
import ssl

logger = logging.getLogger(__name__)


class EmailFetchService:
    """Service for fetching emails from IMAP/POP3 servers"""
    
    def __init__(self, incoming_config):
        self.config = incoming_config
        self.connection = None
    
    def connect(self):
        """Establish connection to mail server"""
        try:
            if self.config.protocol == 'imap':
                return self._connect_imap()
            elif self.config.protocol == 'pop3':
                return self._connect_pop3()
            else:
                raise ValueError(f"Unsupported protocol: {self.config.protocol}")
        except Exception as e:
            logger.error(f"Failed to connect to mail server: {str(e)}")
            raise
    
    def _connect_imap(self):
        """Connect to IMAP server"""
        try:
            # Create SSL context
            if self.config.connection_security == 'ssl':
                context = ssl.create_default_context()
                self.connection = imaplib.IMAP4_SSL(
                    self.config.mail_server,
                    self.config.mail_port,
                    ssl_context=context
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.config.mail_server,
                    self.config.mail_port
                )
                if self.config.connection_security == 'starttls':
                    self.connection.starttls()
            
            # Login
            self.connection.login(self.config.username, self.config.password)
            logger.info(f"Successfully connected to IMAP server: {self.config.mail_server}")
            return True
            
        except Exception as e:
            logger.error(f"IMAP connection error: {str(e)}")
            raise
    
    def _connect_pop3(self):
        """Connect to POP3 server"""
        try:
            if self.config.connection_security == 'ssl':
                context = ssl.create_default_context()
                self.connection = poplib.POP3_SSL(
                    self.config.mail_server,
                    self.config.mail_port,
                    context=context
                )
            else:
                self.connection = poplib.POP3(
                    self.config.mail_server,
                    self.config.mail_port
                )
                if self.config.connection_security == 'starttls':
                    self.connection.stls()
            
            # Login
            self.connection.user(self.config.username)
            self.connection.pass_(self.config.password)
            logger.info(f"Successfully connected to POP3 server: {self.config.mail_server}")
            return True
            
        except Exception as e:
            logger.error(f"POP3 connection error: {str(e)}")
            raise
    
    def fetch_emails(self, inbox, limit=50):
        """Fetch emails from the server"""
        if not self.connection:
            self.connect()
        
        try:
            if self.config.protocol == 'imap':
                return self._fetch_imap_emails(inbox, limit)
            elif self.config.protocol == 'pop3':
                return self._fetch_pop3_emails(inbox, limit)
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise
        finally:
            self.disconnect()
    
    def _fetch_imap_emails(self, inbox, limit=50):
        """Fetch emails from IMAP server"""
        messages_saved = 0
        
        try:
            # Select inbox folder
            self.connection.select(self.config.inbox_folder)
            
            # Search for all emails
            status, message_ids = self.connection.search(None, 'ALL')
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return 0
            
            # Get list of email IDs
            email_ids = message_ids[0].split()
            
            # Fetch only the latest 'limit' emails
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = self.connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Check if message already exists
                    message_id = email_message.get('Message-ID', '')
                    if EmailMessage.objects.filter(inbox=inbox, message_id=message_id).exists():
                        continue
                    
                    # Extract email details
                    subject = self._decode_header(email_message.get('Subject', 'No Subject'))
                    from_email = parseaddr(email_message.get('From', ''))[1]
                    to_emails = self._parse_addresses(email_message.get('To', ''))
                    cc_emails = self._parse_addresses(email_message.get('Cc', ''))
                    date = email_message.get('Date', '')
                    
                    # Extract body
                    body_text, body_html = self._extract_body(email_message)
                    
                    # Create EmailMessage object
                    email_obj = EmailMessage.objects.create(
                        inbox=inbox,
                        message_id=message_id,
                        uid=email_id.decode(),
                        subject=subject,
                        body=body_text or 'No content',
                        html_body=body_html,
                        raw_content=raw_email.decode('utf-8', errors='ignore'),
                        from_email=from_email,
                        to_emails=to_emails,
                        cc_emails=cc_emails,
                        status='received',
                        received_at=timezone.now(),
                    )
                    
                    # Extract attachments
                    self._extract_attachments(email_message, email_obj)
                    
                    messages_saved += 1
                    logger.info(f"Saved email: {subject}")
                    
                except Exception as e:
                    logger.error(f"Error processing email ID {email_id}: {str(e)}")
                    continue
            
            # Update last fetched time
            self.config.last_fetched = timezone.now()
            self.config.save()
            
            return messages_saved
            
        except Exception as e:
            logger.error(f"Error in IMAP fetch: {str(e)}")
            raise
    
    def _fetch_pop3_emails(self, inbox, limit=50):
        """Fetch emails from POP3 server"""
        messages_saved = 0
        
        try:
            # Get message count
            num_messages = len(self.connection.list()[1])
            
            # Fetch only the latest 'limit' emails
            start = max(1, num_messages - limit + 1)
            
            for i in range(start, num_messages + 1):
                try:
                    # Fetch email
                    response, lines, octets = self.connection.retr(i)
                    raw_email = b'\r\n'.join(lines)
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Check if message already exists
                    message_id = email_message.get('Message-ID', '')
                    if EmailMessage.objects.filter(inbox=inbox, message_id=message_id).exists():
                        continue
                    
                    # Extract email details
                    subject = self._decode_header(email_message.get('Subject', 'No Subject'))
                    from_email = parseaddr(email_message.get('From', ''))[1]
                    to_emails = self._parse_addresses(email_message.get('To', ''))
                    cc_emails = self._parse_addresses(email_message.get('Cc', ''))
                    
                    # Extract body
                    body_text, body_html = self._extract_body(email_message)
                    
                    # Create EmailMessage object
                    email_obj = EmailMessage.objects.create(
                        inbox=inbox,
                        message_id=message_id,
                        uid=str(i),
                        subject=subject,
                        body=body_text or 'No content',
                        html_body=body_html,
                        raw_content=raw_email.decode('utf-8', errors='ignore'),
                        from_email=from_email,
                        to_emails=to_emails,
                        cc_emails=cc_emails,
                        status='received',
                        received_at=timezone.now(),
                    )
                    
                    # Extract attachments
                    self._extract_attachments(email_message, email_obj)
                    
                    messages_saved += 1
                    logger.info(f"Saved email: {subject}")
                    
                except Exception as e:
                    logger.error(f"Error processing POP3 email {i}: {str(e)}")
                    continue
            
            # Update last fetched time
            self.config.last_fetched = timezone.now()
            self.config.save()
            
            return messages_saved
            
        except Exception as e:
            logger.error(f"Error in POP3 fetch: {str(e)}")
            raise
    
    def _decode_header(self, header):
        """Decode email header"""
        if not header:
            return ''
        
        decoded_parts = decode_header(header)
        decoded_string = ''
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += str(part)
        
        return decoded_string
    
    def _parse_addresses(self, address_string):
        """Parse email addresses from header"""
        if not address_string:
            return []
        
        addresses = []
        for addr in address_string.split(','):
            email_addr = parseaddr(addr.strip())[1]
            if email_addr:
                addresses.append(email_addr)
        
        return addresses
    
    def _extract_body(self, email_message):
        """Extract text and HTML body from email"""
        body_text = None
        body_html = None
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded_payload = payload.decode(charset, errors='ignore')
                        
                        if content_type == 'text/plain' and not body_text:
                            body_text = decoded_payload
                        elif content_type == 'text/html' and not body_html:
                            body_html = decoded_payload
                except Exception as e:
                    logger.error(f"Error extracting body: {str(e)}")
                    continue
        else:
            # Non-multipart email
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    decoded_payload = payload.decode(charset, errors='ignore')
                    
                    if email_message.get_content_type() == 'text/html':
                        body_html = decoded_payload
                    else:
                        body_text = decoded_payload
            except Exception as e:
                logger.error(f"Error extracting body: {str(e)}")
        
        return body_text, body_html
    
    def _extract_attachments(self, email_message, email_obj):
        """Extract and save attachments"""
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            
            filename = part.get_filename()
            if not filename:
                continue
            
            try:
                # Decode filename
                filename = self._decode_header(filename)
                
                # Get file content
                file_data = part.get_payload(decode=True)
                if not file_data:
                    continue
                
                # Save attachment
                attachment = EmailAttachment.objects.create(
                    message=email_obj,
                    filename=filename,
                    content_type=part.get_content_type() or 'application/octet-stream',
                    size=len(file_data)
                )
                
                # Save file
                attachment.file.save(filename, ContentFile(file_data), save=True)
                logger.info(f"Saved attachment: {filename}")
                
            except Exception as e:
                logger.error(f"Error saving attachment {filename}: {str(e)}")
                continue
    
    def disconnect(self):
        """Disconnect from mail server"""
        try:
            if self.connection:
                if self.config.protocol == 'imap':
                    self.connection.logout()
                elif self.config.protocol == 'pop3':
                    self.connection.quit()
                logger.info("Disconnected from mail server")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")


def fetch_all_inboxes():
    """Fetch emails for all active inboxes"""
    from .models import EmailInbox
    
    results = {}
    inboxes = EmailInbox.objects.filter(is_active=True, incoming_config__isnull=False)
    
    for inbox in inboxes:
        if inbox.incoming_config and inbox.incoming_config.is_active:
            try:
                service = EmailFetchService(inbox.incoming_config)
                count = service.fetch_emails(inbox)
                results[inbox.email_address] = {
                    'success': True,
                    'count': count
                }
                logger.info(f"Fetched {count} emails for {inbox.email_address}")
            except Exception as e:
                results[inbox.email_address] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Failed to fetch emails for {inbox.email_address}: {str(e)}")
    
    return results
