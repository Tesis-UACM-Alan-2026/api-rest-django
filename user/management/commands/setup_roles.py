from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from user.choices import RoleChoices
from user.models import User
from user.permissions import PERMISSION_CODENAMES
import logging
from decouple import config


logger = logging.getLogger('user')

class Command(BaseCommand):
    """
    Crea grupos basados en RoleChoices y asigna permisos personalizados a cada grupo.

    Esta función puede ejecutarse desde el shell o integrarse a una señal para automatizar
    la configuración inicial de seguridad del sistema. Por cada modelo definido en tu app, Django 
    crea automáticamente los siguientes 4 permisos, conocidos como model-level permissions
    Codename	    Nombre (name)	    Propósito principal
    add_<model>	    Can add <Model>	    Crear registros (POST)
    change_<model>	Can change <Model>	Editar registros (PUT/PATCH)
    delete_<model>	Can delete <Model>	Eliminar registros (DELETE)
    view_<model>	Can view <Model>	Ver registros (GET)    

    """

    help = 'Crea superusuario, roles y permisos predeterminados'

    def handle(self, *args, **kwargs):
        SUPERUSER_EMAIL = config('SUPERUSER_EMAIL', default='admin@example.com')
        SUPERUSER_PASSWORD = config('SUPERUSER_PASSWORD', default='admin123')

        if not User.objects.filter(email=SUPERUSER_EMAIL).exists():
            logger.info(f"Creando superusuario por defecto: {SUPERUSER_EMAIL}")
            User.objects.create_superuser(email=SUPERUSER_EMAIL, password=SUPERUSER_PASSWORD)
        else:
            logger.info(f"El superusuario '{SUPERUSER_EMAIL}' ya existe.")

        user_ct = ContentType.objects.get_for_model(User)

        permisos = {}

        group_ct = ContentType.objects.get_for_model(Group)

        for key, codename in PERMISSION_CODENAMES.items():
            if codename == 'can_manage_roles':
                content_type = group_ct
            else:
                content_type = user_ct

            permiso, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': codename.replace('_', ' ').capitalize()}
            )
            permisos[key] = permiso


        permisos_por_rol = {
            RoleChoices.ADMIN.value: [
                permisos['CAN_MANAGE_USERS'],
                permisos['CAN_MANAGE_ROLES'],
                permisos['CAN_MANAGE_PERMISSIONS'],
                permisos['CAN_VIEW_DASHBOARD'],
            ],
            RoleChoices.JEFE_DPTO_ALMACENES.value: [
                permisos['VIEW_USER'],
                permisos['CAN_VIEW_DASHBOARD'],
            ],
            RoleChoices.SEGUNDO_DPTO_ALMACENES.value: [
                permisos['VIEW_USER'],
            ],
            RoleChoices.CAPTURISTA_ENTRADAS.value: [
                permisos['VIEW_USER'],
            ],
            RoleChoices.CAPTURISTA_SALIDAS.value: [
                permisos['VIEW_USER'],
            ],
            RoleChoices.SOLICITANTE.value: [
                permisos['VIEW_USER'],
            ],
        }

        for role in RoleChoices:
            Group.objects.get_or_create(name=role.value)

        for nombre_rol, lista_permisos in permisos_por_rol.items():
            grupo = Group.objects.get(name=nombre_rol)
            grupo.permissions.set(lista_permisos)
            grupo.save()
            logger.info(
                f"{'✓' if nombre_rol not in permisos_por_rol else '-'} Grupo '{nombre_rol}' configurado con {len(lista_permisos)} permisos."
            )