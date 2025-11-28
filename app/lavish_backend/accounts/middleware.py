# accounts/middleware.py

from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone
from datetime import datetime
from dateutil import parser
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, Resolver404
from .models import UserSession
import json
import re
import logging
import time
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        
        try:
            # Check if the session is active
            if 'last_activity' not in request.session:
                request.session['last_activity'] = timezone.now().isoformat()
                return None
            
            # Parse the last activity time
            try:
                last_activity = parser.parse(request.session['last_activity'])
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing last_activity: {e}")
                request.session['last_activity'] = timezone.now().isoformat()
                return None
            
            # Check if user has been inactive for too long
            if (timezone.now() - last_activity).seconds > settings.SESSION_COOKIE_AGE:
                # Save the current URL for later redirect
                if request.path and not (request.path.startswith('/admin/') or
                                         request.path.startswith('/api/') or 
                                         request.path.startswith('/static/')):
                    if hasattr(request.user, 'last_url'):
                        request.user.last_url = request.path
                        request.user.save(update_fields=['last_url'])
                    
                    # Mark the session as inactive
                    if request.session.session_key:
                        try:
                            # Use user and user_agent to identify sessions
                            UserSession.objects.filter(
                                user=request.user,
                                user_agent=request.META.get('HTTP_USER_AGENT', '')
                            ).update(is_active=False)
                        except Exception as e:
                            logger.error(f"Error updating session status: {e}")
                    
                # Logout the user
                logout(request)
                logger.info(f"User {request.user.username} logged out due to inactivity")
            
            # Update the last activity time
            request.session['last_activity'] = timezone.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error in AutoLogoutMiddleware: {e}")
        
        return None

class SessionTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        if request.user.is_authenticated:
            # Update last activity time
            request.user.last_activity = timezone.now()
            request.user.save(update_fields=['last_activity'])
            
            # Store current URL if it's not an AJAX request, media, static, or admin
            current_path = request.get_full_path()
            if (not request.is_ajax() if hasattr(request, 'is_ajax') else not request.headers.get('x-requested-with') == 'XMLHttpRequest') and \
               not current_path.startswith(('/admin/', '/static/', '/media/')) and \
               request.method == 'GET':
                request.user.last_url = current_path
                request.user.save(update_fields=['last_url'])
                
                # Track session
                session_key = request.session.session_key
                if session_key:
                    try:
                        # Use the correct fields that exist in the UserSession model
                        defaults = {
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                            'ip_address': self._get_client_ip(request),
                            'is_active': True,
                            'login_method': 'password',  # Default login method
                            'last_activity': timezone.now()
                        }
                        
                        # Try to get or create the session
                        user_session, created = UserSession.objects.get_or_create(
                            user=request.user,
                            session_key=session_key,
                            defaults=defaults
                        )
                        
                        if not created:
                            # Update last_activity and last_url if session already exists
                            user_session.last_activity = timezone.now()
                            if hasattr(user_session, 'last_url'):
                                user_session.last_url = current_path
                            user_session.save()
                    except Exception as e:
                        logger.error(f"Error tracking user session: {e}")

            # Check for session timeout
            timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 1800)  # Default 30 minutes
            if timeout:
                last_activity = request.user.last_activity
                if last_activity and (timezone.now() - last_activity).total_seconds() > timeout:
                    logger.info(f"Session timeout for user {request.user.username}")
                    logout(request)

        response = self.get_response(request)
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
