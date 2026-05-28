from django.apps import AppConfig

class UserConfig(AppConfig):
    """
    Configuración de la aplicación 'user'.

    Esta clase define parámetros de configuración para la app,
    como el tipo de campo de clave primaria por defecto y acciones
    que deben ejecutarse cuando la app esté lista (por ejemplo, registrar señales).
    """
    default_auto_field = 'django.db.models.BigAutoField'  # Tipo de campo auto incremental por defecto
    name = 'user'  # Nombre de la app Django

    def ready(self):
        """
        Método llamado automáticamente cuando la app 'user' ha sido cargada por Django.

        Se utiliza para importar señales y asegurar que estén registradas al inicio.
        """
        import user.signals  # Importación de señales (handlers de eventos como post_save)
