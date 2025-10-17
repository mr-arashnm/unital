# apps/complexes/apps.py
from django.apps import AppConfig

class ComplexesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.complexes'

    def ready(self):
        from . import signals  # Use relative import