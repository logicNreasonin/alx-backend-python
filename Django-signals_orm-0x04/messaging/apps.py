# messaging/apps.py
from django.apps import AppConfig

class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging' # This should match the name of your app directory

    def ready(self):
        """
        Import signals when the app is ready.
        This is the recommended way to register signals.
        """
        import messaging.signals # noqa F401: Import signals to connect them
        print("DEBUG: Messaging signals imported and ready.") # For console debugging