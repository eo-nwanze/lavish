from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging
from .face_auth import authenticate_with_face

# Get logger
logger = logging.getLogger(__name__)

# Get the user model
User = get_user_model()

class FacialAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend to authenticate users via facial recognition.
    """
    
    def authenticate(self, request, username=None, password=None, facial_login=False, **kwargs):
        """
        Authenticate a user based on facial recognition.
        
        Args:
            request: The request object
            username: Optional username to restrict facial search to a specific user
            password: Not used for facial auth but required by the interface
            facial_login: Flag to indicate facial login is being attempted
            
        Returns:
            User or None: The authenticated user if successful, None otherwise
        """
        # Only process if facial login flag is set
        if not facial_login:
            return None
            
        # Attempt to authenticate with face
        if request and hasattr(request, 'META') and request.META.get('HTTP_X_API_REQUEST', False):
            # API request - use headless mode
            headless = True
        else:
            # Browser request - use interactive mode
            headless = False
            
        # Log the authentication attempt
        logger.info(f"Facial authentication attempt: {'with username' if username else 'without username'}")
        
        # Authenticate with face
        user = authenticate_with_face(
            require_username=bool(username),
            username=username,
            headless=headless
        )
        
        # Log the result
        if user:
            logger.info(f"Facial authentication successful for user: {user.username}")
        else:
            logger.warning("Facial authentication failed")
            
        return user 