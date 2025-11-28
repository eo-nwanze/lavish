# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from .models import CustomUser, Company, BankDetail, CardDetail, StoragePlan, UserSubscription, SubscriptionTransaction
from .forms import CustomUserCreationForm, CustomUserLoginForm, CompanyCreationForm, BankDetailForm, CardDetailForm, CustomPasswordResetForm
from django.core.files.base import ContentFile
from django.conf import settings
from .tools import send_verification_email, generate_totp_secret, generate_totp_qr_code, verify_otp, send_login_notification
import base64
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.views import PasswordResetView, LoginView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import traceback
from django.utils import timezone
from datetime import timedelta
# from email_manager.utils import send_template_email
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from accounts.models import UserSession
from django.contrib.auth.forms import AuthenticationForm
from .face_detection_adapter import link_facial_identity_to_user
from django.core.files.storage import FileSystemStorage
import os
from django.db.models import Q
from accounts.face_auth import register_user_face, authenticate_with_face
from accounts.models import FacialIdentity, UserSession

logger = logging.getLogger(__name__)

# Individual Signup View
def signup_individual_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Disable account until email is verified
            user.bio = ""  # Set a default empty string for bio
            user.save()
            
            # Send verification email with error handling
            success, message = send_verification_email(user, request)
            if success:
                messages.success(request, 'Check your email to verify your account.')
            else:
                if settings.DEBUG:
                    # In development, show a message with the activation link
                    messages.warning(request, message)
                else:
                    messages.warning(request, 'Account created but email verification failed. Please contact support.')
            
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup_individual.html', {'form': form})

# Company Signup View
def signup_company_view(request):
    if request.method == 'POST':
        form = CompanyCreationForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            # Create a user as the admin of the company with email verification
            user = CustomUser.objects.create(
                username=request.POST['username'],
                email=request.POST['email'],
                company=company,
                is_company_admin=True,
                is_active=False,  # Disable until email verification
                bio=""  # Set a default empty string for bio
            )
            user.set_password(request.POST['password1'])  # Set the password from the POST data
            user.save()
            
            # Send verification email with error handling
            success, message = send_verification_email(user, request)
            if success:
                messages.success(request, 'Company created. Check your email to verify your account.')
            else:
                if settings.DEBUG:
                    # In development, show a message with the activation link
                    messages.warning(request, message)
                else:
                    messages.warning(request, 'Company created but email verification failed. Please contact support.')
            
            return redirect('accounts:login')
    else:
        form = CompanyCreationForm()
    return render(request, 'accounts/signup_company.html', {'form': form})

# Email Activation View
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.email_verified = True
        user.save()
        messages.success(request, 'Your account has been verified. You can now log in.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Activation link is invalid or expired.')
        return redirect('accounts:signup_individual')

# Login View
def login_view(request):
    """
    Custom login view that supports both standard and facial authentication.
    """
    # Check if this is a facial authentication request
    if request.method == 'POST' and request.POST.get('facial_auth') == 'true':
        # Handle facial authentication
        return handle_facial_login(request)
    
    # Store next parameter in session if provided
    if 'next' in request.GET:
        request.session['next'] = request.GET.get('next')
    
    # Regular form-based authentication
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Check if MFA is enabled for this user
                if user.mfa_enabled:
                    # Store user ID in session for MFA verification
                    request.session['awaiting_mfa'] = True
                    request.session['awaiting_mfa_user_id'] = user.id
                    
                    # Redirect to MFA verification
                    return redirect('accounts:mfa_verify')
                
                # Standard login if MFA not enabled
                login(request, user)
                
                # Create user session entry
                record_login(request, user, method='password')
                
                # Send login notification email
                send_login_notification(user, request)
                
                # Log the successful login
                logger.info(f"User {username} logged in via password")
                
                # Redirect to the appropriate page
                next_page = request.session.pop('next', 'home')
                return redirect(next_page)
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def handle_facial_login(request):
    """
    Process a facial authentication login request.
    """
    if request.method != 'POST' or 'facial_image' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
    facial_image = request.FILES['facial_image']
    
    # Temporary file path for the uploaded image
    fs = FileSystemStorage(location='media/facial_auth/temp/')
    filename = fs.save('temp_auth.jpg', facial_image)
    image_path = fs.path(filename)
    
    try:
        # Use the face detection system to identify the user
        from face_detection.face_auth import verify_face
        user_id, confidence = verify_face(image_path)
        
        if user_id:
            # Get the user
            try:
                user = CustomUser.objects.get(username=user_id)
                
                # Check if facial auth is enabled for this user
                if not user.face_login_enabled:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Facial authentication is disabled for this account'
                    }, status=403)
                
                # Get facial identity
                try:
                    facial_identity = FacialIdentity.objects.get(user=user)
                    
                    # Check if facial identity is enabled
                    if not facial_identity.enabled:
                        return JsonResponse({
                            'status': 'error', 
                            'message': 'Facial authentication is disabled for this account'
                        }, status=403)
                    
                    # Check confidence level - convert from 0-1 to 0-100 percentage
                    confidence_percent = confidence * 100
                    if confidence_percent < facial_identity.min_confidence:
                        return JsonResponse({
                            'status': 'error', 
                            'message': f'Face not recognized with sufficient confidence ({confidence_percent:.1f}% < {facial_identity.min_confidence}%)'
                        }, status=403)
                    
                    # Check if MFA is enabled for this user
                    if user.mfa_enabled:
                        # Store user ID in session for MFA verification
                        request.session['awaiting_mfa'] = True
                        request.session['awaiting_mfa_user_id'] = user.id
                        
                        # Return redirect to MFA verification
                        return JsonResponse({
                            'status': 'success', 
                            'redirect': reverse('accounts:mfa_verify'),
                            'message': 'MFA verification required'
                        })
                    
                    # Login the user with explicit backend to avoid issues with multiple auth backends
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    
                    # Update last used timestamp
                    facial_identity.last_used = timezone.now()
                    facial_identity.save(update_fields=['last_used'])
                    
                    # Create session record
                    record_login(request, user, method='facial')
                    
                    # Log the successful login
                    logger.info(f"User {user.username} logged in via facial authentication")
                    
                    # Determine the redirect URL
                    next_page = request.session.pop('next', 'home')
                    
                    # Return success with confidence information
                    return JsonResponse({
                        'status': 'success', 
                        'redirect': reverse(next_page) if next_page != 'home' else '/',
                        'confidence': f"{confidence_percent:.1f}%"
                    })
                    
                except FacialIdentity.DoesNotExist:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'No facial identity associated with this account'
                    }, status=404)
                    
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'User not found'
                }, status=404)
        else:
            return JsonResponse({
                'status': 'error', 
                'message': 'Face not recognized. Please ensure your face is clearly visible.'
            }, status=403)
    
    except Exception as e:
        logger.error(f"Error during facial authentication: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': 'Error processing facial authentication'
        }, status=500)
    finally:
        # Clean up temporary file
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def record_login(request, user, method='password'):
    """
    Record a login event with details about the session
    
    Args:
        request: The HTTP request
        user: The authenticated user
        method: Authentication method used ('password', 'facial', 'mfa', etc.)
    """
    try:
        # Get client IP and user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create a new UserSession record
        UserSession.objects.create(
            user=user,
            session_key=request.session.session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            login_method=method
        )
        
        # Log the login event
        logger.info(f"User {user.username} logged in with {method} authentication from {ip_address}")
        
    except Exception as e:
        # Don't fail login if record keeping fails
        logger.error(f"Error recording login event: {str(e)}")

# MFA Setup View
@login_required
def mfa_setup(request):
    user = request.user

    # If MFA is already enabled, go directly to MFA verification
    if user.mfa_enabled:
        return redirect('accounts:mfa_verify')

    # Generate a new secret key if the user does not have one
    if not user.otp_secret:
        user.otp_secret = generate_totp_secret()
        user.save()

    # Generate the QR code for the TOTP secret key
    qr_code_base64, uri = generate_totp_qr_code(user.otp_secret, user.username)
    
    # If there was an error generating the QR code
    if not qr_code_base64:
        messages.error(request, "Error generating QR code. Please try again.")
        return redirect('accounts:login')
        
    # Create data URL for the QR code
    qr_code_data_url = f"data:image/png;base64,{qr_code_base64}"

    # If form is submitted (button click), redirect to MFA verification page
    if request.method == 'POST':
        return redirect('accounts:mfa_verify')

    # Render the MFA setup template with the QR code image
    return render(request, 'accounts/mfa_setup.html', {'qr_code_data_url': qr_code_data_url})

# MFA Verification View
def mfa_verify(request):
    # Check if we have a user awaiting MFA verification
    awaiting_mfa = request.session.get('awaiting_mfa', False)
    user_id = request.session.get('awaiting_mfa_user_id')
    
    if not awaiting_mfa or not user_id:
        messages.error(request, 'Invalid MFA verification attempt. Please login again.')
        return redirect('accounts:login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found. Please login again.')
        request.session.pop('awaiting_mfa', None)
        request.session.pop('awaiting_mfa_user_id', None)
        return redirect('accounts:login')

    # Handle POST request for OTP verification
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        logger.info(f"MFA verification attempt for user: {user.username}")

        # Check if the OTP code entered by the user is valid
        if otp_code and verify_otp(user.otp_secret, otp_code):
            # If OTP is valid, enable MFA and redirect to the home page
            user.mfa_enabled = True  # Enable MFA after successful verification
            user.save()
            
            # Clear MFA verification flags
            request.session.pop('awaiting_mfa', None)
            request.session.pop('awaiting_mfa_user_id', None)
            
            # Log in the user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            # Record the login
            record_login(request, user, method='2fa')
            
            # Set session flag for MFA verification
            request.session['mfa_verified'] = True
            request.session.save()
            
            # Add success message
            messages.success(request, 'MFA verified successfully. Welcome!')
            
            # Log the verification
            logger.info(f"User {user.username} successfully verified MFA")
            
            # Redirect to home page
            next_page = request.session.get('next', 'home:index')
            return redirect(next_page if ':' in next_page else '/')
        else:
            # If OTP is invalid, show an error message and remain on the same page
            logger.warning(f"Invalid OTP code entered by {user.username}")
            messages.error(request, 'Invalid OTP code. Please try again.')

    # Render the MFA verification template where user enters OTP
    return render(request, 'accounts/mfa_verify.html', {'user': user})

# Logout View
def logout_view(request):
    if request.user.is_authenticated:
        # Mark all user sessions as inactive
        from accounts.models import UserSession
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)
        
        # Log the logout
        logger.info(f"User {request.user.username} logged out")
    
    # Perform the logout
    logout(request)
    return redirect('accounts:login')


# Bank Details Views
@login_required
def add_bank_detail(request):
    if request.method == "POST":
        form = BankDetailForm(request.POST)
        if form.is_valid():
            bank_detail = form.save(commit=False)
            bank_detail.user = request.user
            bank_detail.save()
            messages.success(request, "Bank detail added successfully!")
            return redirect("accounts:list_bank_details")
    else:
        form = BankDetailForm()
    return render(request, "accounts/add_bank_detail.html", {"form": form})


@login_required
def list_bank_details(request):
    bank_details = BankDetail.objects.filter(user=request.user)
    return render(request, "accounts/list_bank_details.html", {"bank_details": bank_details})


# Card Details Views
@login_required
def add_card_detail(request):
    if request.method == "POST":
        form = CardDetailForm(request.POST)
        if form.is_valid():
            card_detail = form.save(commit=False)
            card_detail.user = request.user
            card_detail.save()
            messages.success(request, "Card detail added successfully!")
            return redirect("accounts:list_card_details")
    else:
        form = CardDetailForm()
    return render(request, "accounts/add_card_detail.html", {"form": form})


@login_required
def list_card_details(request):
    card_details = CardDetail.objects.filter(user=request.user)
    return render(request, "accounts/list_card_details.html", {"card_details": card_details})

@login_required
def profile(request):
    """
    Show account details and authentication settings
    Includes facial authentication status and management
    """
    # Get user's stripe customer ID if exists
    has_customer = False
    # Safely check if stripe_customer_id attribute exists and has a value
    if hasattr(request.user, 'stripe_customer_id') and request.user.stripe_customer_id:
        has_customer = True

    # Check if user has facial authentication setup
    has_facial = False
    facial_enabled = False
    facial_image = None
    face_registered_date = None
    face_last_used = None
    
    try:
        facial_identity = FacialIdentity.objects.get(user=request.user)
        has_facial = True
        facial_enabled = facial_identity.enabled
        facial_image = facial_identity.face_image_path
        face_registered_date = facial_identity.date_registered
        face_last_used = facial_identity.last_used
    except FacialIdentity.DoesNotExist:
        pass

    context = {
        'user': request.user,
        'has_customer': has_customer,
        'has_facial': has_facial,
        'facial_enabled': facial_enabled,
        'facial_image': facial_image,
        'face_registered_date': face_registered_date,
        'face_last_used': face_last_used,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    
    return render(request, 'accounts/profile.html', context)

# Add this class-based view for AJAX password reset
@method_decorator(csrf_exempt, name='dispatch')
class AjaxPasswordResetView(PasswordResetView):
    """Class-based view that handles password reset with AJAX support"""
    
    def form_valid(self, form):
        """Override form_valid to handle AJAX requests"""
        # Get the email from the form
        email = form.cleaned_data['email']
        
        # Log successful reset attempt for debugging
        logger.info(f"Password reset requested for email: {email}")
        
        try:
            # Check if a user with this email exists
            users = list(form.get_users(email))
            if not users:
                error_msg = f"No user found with email address {email}"
                logger.warning(error_msg)
                
                # For AJAX requests
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=404)
                
                # For standard requests
                messages.error(self.request, error_msg)
                return self.form_invalid(form)
            
            # Process the form - this sends the email
            super().form_valid(form)
            logger.info(f"Password reset email sent successfully to {email}")
            
            # Check if it's an AJAX request
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return success response with redirect URL
                return JsonResponse({
                    'success': True,
                    'message': f'Password reset email sent to {email}',
                    'redirect_url': self.success_url
                })
            
            # Regular form submission
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            if settings.DEBUG:
                traceback.print_exc()
            
            # Check if it's an AJAX request
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return error response
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to send password reset email: {str(e)}'
                }, status=500)
            
            # Regular form submission - add message and redisplay form
            messages.error(self.request, f"Failed to send password reset email: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Override form_invalid to handle AJAX requests"""
        # Log form errors
        logger.warning(f"Invalid password reset form: {form.errors}")
        
        # Check if it's an AJAX request
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Return error response
            return JsonResponse({
                'success': False,
                'error': 'Invalid form submission',
                'errors': form.errors.as_json()
            }, status=400)
        
        # Regular form submission
        return super().form_invalid(form)

@login_required
def subscription_manage(request):
    """View to manage storage subscription"""
    # Get all available plans
    plans = StoragePlan.objects.filter(is_active=True)
    
    # Get user's current subscription
    try:
        subscription = request.user.storage_subscription
    except UserSubscription.DoesNotExist:
        # Create default subscription with Basic plan
        basic_plan = StoragePlan.objects.filter(name='Basic').first()
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=basic_plan,
            status='active',
            next_billing_date=timezone.now() + timedelta(days=30)
        )
    
    context = {
        'plans': plans,
        'subscription': subscription,
    }
    return render(request, 'accounts/subscription.html', context)

@login_required
def subscription_checkout(request, plan_id):
    """Checkout page for plan subscription"""
    plan = get_object_or_404(StoragePlan, id=plan_id, is_active=True)
    
    # Get user's current subscription
    try:
        subscription = request.user.storage_subscription
    except UserSubscription.DoesNotExist:
        subscription = None
    
    # If user already has this plan, redirect back
    if subscription and subscription.plan == plan:
        messages.info(request, f"You are already subscribed to the {plan.name} plan.")
        return redirect('accounts:subscription')
    
    context = {
        'plan': plan,
        'subscription': subscription,
    }
    return render(request, 'accounts/subscription_checkout.html', context)

@login_required
def subscription_confirm(request, plan_id):
    """Confirm subscription to a plan"""
    if request.method != 'POST':
        return redirect('accounts:subscription')
    
    plan = get_object_or_404(StoragePlan, id=plan_id, is_active=True)
    billing_cycle = request.POST.get('billing_cycle', 'monthly')
    
    # Calculate amount based on billing cycle
    if billing_cycle == 'yearly':
        amount = plan.price_yearly
        next_billing_date = timezone.now() + timedelta(days=365)
    else:
        amount = plan.price_monthly
        next_billing_date = timezone.now() + timedelta(days=30)
    
    # Get or create user subscription
    subscription, created = UserSubscription.objects.get_or_create(
        user=request.user,
        defaults={
            'plan': plan,
            'billing_cycle': billing_cycle,
            'status': 'active',
            'next_billing_date': next_billing_date
        }
    )
    
    # If subscription exists, update it
    if not created:
        old_plan = subscription.plan
        subscription.plan = plan
        subscription.billing_cycle = billing_cycle
        subscription.status = 'active'
        subscription.next_billing_date = next_billing_date
        subscription.save()
    
    # Create a transaction record
    SubscriptionTransaction.objects.create(
        subscription=subscription,
        amount=amount,
        status='completed',
        transaction_id=f"sub_{int(timezone.now().timestamp())}",
        payment_method='card'
    )
    
    # Send subscription confirmation email
    try:
        context = {
            'plan_name': plan.name,
            'billing_cycle': billing_cycle,
            'amount': amount,
            'next_billing_date': next_billing_date.strftime('%Y-%m-%d'),
            'storage_limit': plan.get_formatted_storage(),
        }
        send_template_email(
            subject=f"Your {plan.name} Plan Subscription",
            template_name='subscription_confirmation',
            to_email=request.user.email,
            context=context
        )
    except Exception as e:
        # Log error but don't stop the subscription process
        print(f"Error sending subscription email: {str(e)}")
    
    messages.success(
        request, 
        f"Successfully subscribed to the {plan.name} plan with {billing_cycle} billing. "
        f"Your storage limit is now {plan.get_formatted_storage()}."
    )
    return redirect('accounts:subscription')

@login_required
def subscription_cancel(request):
    """Cancel subscription"""
    if request.method != 'POST':
        return redirect('accounts:subscription')
    
    try:
        subscription = request.user.storage_subscription
        
        # If user is on Basic (free) plan, don't allow cancellation
        if subscription.plan.name == 'Basic':
            messages.info(request, "You are on the Basic plan which is free. There's nothing to cancel.")
            return redirect('accounts:subscription')
        
        # Get basic plan
        basic_plan = StoragePlan.objects.filter(name='Basic').first()
        
        # Get the amount of storage currently used
        current_usage = subscription.get_storage_usage()
        
        # Check if downgrading would exceed Basic plan's limit
        if current_usage > basic_plan.storage_limit:
            messages.error(
                request,
                f"Unable to cancel your subscription. You are currently using "
                f"{subscription.get_formatted_usage()} which exceeds the Basic plan limit "
                f"of {basic_plan.get_formatted_storage()}. Please reduce your storage usage first."
            )
            return redirect('accounts:subscription')
        
        # Update subscription to basic plan
        subscription.plan = basic_plan
        subscription.billing_cycle = 'monthly'
        subscription.status = 'canceled'
        subscription.canceled_at = timezone.now()
        subscription.save()
        
        # Send cancellation email
        try:
            context = {
                'previous_plan': subscription.plan.name,
                'basic_plan_limit': basic_plan.get_formatted_storage(),
            }
            send_template_email(
                subject="Your Subscription Has Been Canceled",
                template_name='subscription_canceled',
                to_email=request.user.email,
                context=context
            )
        except Exception as e:
            # Log error but don't stop the cancellation process
            print(f"Error sending cancellation email: {str(e)}")
        
        messages.success(
            request, 
            "Your subscription has been canceled. Your account has been downgraded to the Basic plan."
        )
    except UserSubscription.DoesNotExist:
        messages.error(request, "No active subscription found.")
    
    return redirect('accounts:subscription')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('dashboard')  # Default redirect if no last URL

    def form_valid(self, form):
        """
        Security check complete. Log the user in and handle last URL redirection.
        """
        # Perform standard login
        response = super().form_valid(form)
        
        # Update last activity time
        try:
            self.request.user.last_activity = timezone.now()
            self.request.user.save(update_fields=['last_activity'])
        except Exception as e:
            logger.error(f"Error updating last_activity: {e}")
        
        # Send login notification email
        try:
            success, message = send_login_notification(self.request.user, self.request)
            if not success:
                logger.warning(f"Login notification email not sent: {message}")
        except Exception as e:
            logger.error(f"Error sending login notification: {str(e)}")
        
        # Check if there's a UserSession record with a last_url to resume
        redirect_url = self.get_success_url()
        
        try:
            user_sessions = UserSession.objects.filter(
                user=self.request.user, 
                is_active=True
            ).order_by('-updated_at')
            
            # Try to find a resumable URL
            if user_sessions.exists():
                last_session = user_sessions.first()
                if last_session.last_url and last_session.last_url != '/login/' and last_session.last_url != '/logout/':
                    redirect_url = last_session.last_url
            
            # If no session, check user's last_url
            elif hasattr(self.request.user, 'last_url') and self.request.user.last_url:
                if self.request.user.last_url != '/login/' and self.request.user.last_url != '/logout/':
                    redirect_url = self.request.user.last_url
            
            # Create a new UserSession
            if self.request.session.session_key:
                UserSession.objects.get_or_create(
                    user=self.request.user,
                    session_key=self.request.session.session_key,
                    defaults={
                        'ip_address': self._get_client_ip(),
                        'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
                        'last_url': redirect_url
                    }
                )
        except Exception as e:
            logger.error(f"Error handling session or URL redirection: {e}")
        
        # Check if the URL is safe to redirect to - use url_has_allowed_host_and_scheme instead of is_safe_url
        try:
            url_is_safe = url_has_allowed_host_and_scheme(
                url=redirect_url,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
            )
            
            if not url_is_safe:
                redirect_url = self.success_url
        except Exception as e:
            logger.error(f"Error checking URL safety: {e}")
            redirect_url = self.success_url
            
        return HttpResponseRedirect(redirect_url)
    
    def _get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

@login_required
def facial_setup(request):
    """
    View for setting up facial authentication
    """
    # Check if user already has facial auth setup
    try:
        facial_identity = FacialIdentity.objects.get(user=request.user)
        messages.info(request, "You already have facial authentication set up. You can re-register your face if needed.")
    except FacialIdentity.DoesNotExist:
        pass
    
    # Handle form submission
    if request.method == 'POST':
        # Register the user's face
        result = register_user_face(request.user, headless=False)
        
        if result['success']:
            messages.success(request, "Facial authentication has been set up successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, result['message'])
    
    return render(request, 'accounts/facial_setup.html')

@login_required
def facial_toggle(request):
    """
    View for toggling facial authentication on/off
    """
    if request.method == 'POST':
        try:
            facial_identity = FacialIdentity.objects.get(user=request.user)
            
            # Toggle the enabled status
            facial_identity.enabled = not facial_identity.enabled
            facial_identity.save()
            
            # Also update the user's face_login_enabled field
            request.user.face_login_enabled = facial_identity.enabled
            request.user.save(update_fields=['face_login_enabled'])
            
            status = "enabled" if facial_identity.enabled else "disabled"
            messages.success(request, f"Facial authentication has been {status}.")
            
        except FacialIdentity.DoesNotExist:
            messages.error(request, "You need to set up facial authentication first.")
    
    return redirect('accounts:profile')

def check_facial_available(request):
    """
    Check if there are any users with facial authentication enabled.
    This is used by the login page to determine whether to show the facial login button.
    """
    # Check if any users have facial auth enabled
    has_enabled_users = CustomUser.objects.filter(
        Q(face_login_enabled=True) & 
        Q(facial_identity__enabled=True)
    ).exists()
    
    return JsonResponse({
        'facial_available': has_enabled_users
    })

def facial_login(request):
    """
    View for handling facial authentication login
    """
    if request.method == 'POST':
        # Facial recognition based authentication
        user = authenticate_with_face(headless=False)
        
        if user is not None:
            # User authenticated via face, now log them in
            from django.contrib.auth import login as auth_login
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Record the login in session
            if hasattr(user, 'usersession_set'):
                session = UserSession.objects.create(
                    user=user,
                    session_key=request.session.session_key,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            # Send login notification email
            try:
                success, message = send_login_notification(user, request)
                if not success:
                    logger.warning(f"Login notification email not sent: {message}")
            except Exception as e:
                logger.error(f"Error sending login notification: {str(e)}")
            
            # Redirect to success page
            next_url = request.POST.get('next', None)
            if next_url:
                return redirect(next_url)
            return redirect('home:index')
        else:
            # Authentication failed
            messages.error(request, "Facial authentication failed. Please try again or use password login.")
            
    # If not POST or authentication failed, redirect to login page
    return redirect('accounts:login')
