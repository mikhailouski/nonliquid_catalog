from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
    
    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import apps.catalog.signals