# accounts/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm

app_name = 'accounts'

urlpatterns = [
    path('signup/individual/', views.signup_individual_view, name='signup_individual'),
    path('signup/company/', views.signup_company_view, name='signup_company'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('mfa-setup/', views.mfa_setup, name='mfa_setup'),
    path('mfa-verify/', views.mfa_verify, name='mfa_verify'),
    path('profile/', views.profile, name='profile'),

    # New paths for bank and card details
    path("bank/add/", views.add_bank_detail, name="add_bank_detail"),
    path("bank/list/", views.list_bank_details, name="list_bank_details"),
    path("card/add/", views.add_card_detail, name="add_card_detail"),
    path("card/list/", views.list_card_details, name="list_card_details"),
    
    # Password reset URLs with CustomPasswordResetForm
    path('password_reset/', 
         views.AjaxPasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            form_class=CustomPasswordResetForm,
            email_template_name='accounts/password_reset_email.html',
            html_email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/accounts/password_reset/done/'
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/accounts/reset/done/'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    # Subscription management
    path('subscription/', views.subscription_manage, name='subscription'),
    path('subscription/checkout/<int:plan_id>/', views.subscription_checkout, name='subscription_checkout'),
    path('subscription/confirm/<int:plan_id>/', views.subscription_confirm, name='subscription_confirm'),
    path('subscription/cancel/', views.subscription_cancel, name='subscription_cancel'),
    
    # Facial authentication
    path('facial-setup/', views.facial_setup, name='facial_setup'),
    path('facial-toggle/', views.facial_toggle, name='facial_toggle'),
    path('facial-login/', views.facial_login, name='facial_login'),
    path('check-facial-available/', views.check_facial_available, name='check_facial_available'),
]
