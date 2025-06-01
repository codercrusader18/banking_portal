from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import signals or other post-init code
        #import core.signals  # Only if you have signals

        # Custom user model registration
        from django.contrib import admin
        from django.contrib.auth import get_user_model
        from .admin import CustomUserAdmin  # Import your custom admin

        User = get_user_model()

        # Only register if not already registered
        if not admin.site.is_registered(User):
            admin.site.register(User, CustomUserAdmin)