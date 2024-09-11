from django.apps import AppConfig


class ElearningPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'elearning_platform'

    def ready(self):
        import elearning_platform.signals
