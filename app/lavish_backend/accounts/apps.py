from django.apps import AppConfig, apps


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """Override auth app verbose name when app is ready"""
        try:
            auth_app = apps.get_app_config('auth')
            auth_app.verbose_name = 'Authorization'
        except Exception:
            pass
