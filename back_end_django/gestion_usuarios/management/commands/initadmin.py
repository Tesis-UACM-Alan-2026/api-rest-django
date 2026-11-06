###############codigo 11#############################
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Crea un superusuario inicial para pruebas JWT"

    def handle(self, *args, **kwargs):

        username = "Admin"
        email = "admin@tecnologias.com"
        password = "AdmApiDjango123"

        # Verificar si ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"El usuario '{username}' ya existe."
                )
            )
            return

        # Crear superusuario
        self.user = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin12345"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superusuario '{username}' creado correctamente."
            )
        )