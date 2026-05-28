from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .choices import RoleChoices  #Importa tu enumeración
from .managers import UserManager 
import uuid
from django.conf import settings
from django.core.validators import FileExtensionValidator


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado basado en AbstractBaseUser y  PermissionsMixin.

    Hereda de:
        - AbstractBaseUser: para tener campos base como password y last_login.
        - PermissionsMixin: para incluir automáticamente is_superuser, groups, user_permissions.

    Notas:
        - El campo 'is_active' debe declararse manualmente.
        - 'password' y 'last_login' son heredados desde AbstractBaseUser
        - 'is_superuser', 'groups' y 'user_permissions' son heredados desde PermissionsMixin.
 
    Este modelo incluye campos adicionales para realizar auditoría completa sobre el ciclo de vida del usuario,
    incluyendo creación, actualización, eliminación lógica, restauración, bloqueo y desbloqueo.

    Campos de trazabilidad:
        - date_joined: Fecha de alta inicial del usuario (registro).
        - created_at: Fecha en que se creó el registro en la base de datos.
        - updated_at: Última vez que se actualizó el registro.
        - created_by: Usuario que creó el registro.
        - updated_by: Usuario que actualizó por última vez.
        - is_deleted: Indicador lógico de eliminación.
        - deleted_at: Fecha en que fue eliminado lógicamente.
        - deleted_by: Usuario que eliminó lógicamente el registro.
        - restored_at: Fecha en que fue restaurado.
        - restored_by: Usuario que restauró el registro.
        - blocked_at: Fecha en que el usuario fue desactivado (is_active = False).
        - blocked_by: Usuario que realizó el bloqueo.
        - unblocked_at: Fecha en que el usuario fue reactivado.
        - unblocked_by: Usuario que realizó el desbloqueo.

    Estos campos permiten mantener una trazabilidad completa sobre el historial de cambios
    y acciones administrativas realizadas sobre los usuarios.
    """


    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    #Campo para mostrar el rol principal asignado
    role = models.CharField(  
        max_length=100,
        choices=RoleChoices.choices,
        default=RoleChoices.SOLICITANTE
    )


    # Autenticación
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    signing_password = models.CharField(max_length=255)  # Contraseña para firma digital u otros propósitos

    # Información de acceso
    last_login_IP = models.GenericIPAddressField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)  # Requerido por el sistema de administración
    is_active = models.BooleanField(default=True)  # Este campo debe estar presente si se usa autenticación
    blocked_at = models.DateTimeField(null=True, blank=True)

    # Perfil
    profile_picture = models.CharField(max_length=255, null=True, blank=True)


    
    #DATOS PERSONALES
    # Identidad
    name = models.CharField(max_length=50)
    middlename = models.CharField(max_length=50, null=True, blank=True)
    first_lastname = models.CharField(max_length=50)
    second_lastname = models.CharField(max_length=50, null=True, blank=True)
    birthdate = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)  # Se recomienda usar choices

    # Documentos oficiales
    curp = models.CharField(max_length=18, unique=True)

    # Contacto
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    cellphone = models.CharField(max_length=255, null=True, blank=True)

    # Dirección
    address_cat_nacionalidad_id = models.BigIntegerField(null=True, blank=True)
    address_cat_entidad_id = models.BigIntegerField(null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_zip_code = models.CharField(max_length=10, null=True, blank=True)
    address_neighborhood = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    address_number = models.CharField(max_length=25, null=True, blank=True)
    address_interior_number = models.CharField(max_length=25, null=True, blank=True)
    address_complement = models.TextField(null=True, blank=True)

    #EMPLEADO
    
    # Datos laborales
    job_position = models.CharField(max_length=255, null=True, blank=True)
    employee_number = models.CharField(max_length=255, null=True, blank=True, unique=True)
    license = models.CharField(max_length=255, null=True, blank=True, unique=True)
    rfc = models.CharField(max_length=13, null=True, blank=True, unique=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)  # Recomendado usar enum o choices

    # Observaciones
    notes = models.TextField(null=True, blank=True)

   
    # Tiempos y trazabilidad general

    # Fecha en que el usuario se registró por primera vez (autenticación).
    date_joined = models.DateTimeField(default=timezone.now)

    # Fecha en que el registro fue creado en la base de datos.
    created_at = models.DateTimeField(auto_now_add=True)

    # Fecha de la última modificación del registro.
    updated_at = models.DateTimeField(auto_now=True)

    # Indicador de eliminación lógica (sin borrar físicamente el registro).
    is_deleted = models.BooleanField(default=False)

    # Fecha en que el registro fue eliminado lógicamente.
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Fecha en que el registro fue restaurado después de haber sido eliminado.
    restored_at = models.DateTimeField(null=True, blank=True)
    
    # Fecha en que el usuario fue reactivado (desbloqueado).
    unblocked_at = models.DateTimeField(null=True, blank=True)
    
    # Usuario que creó el registro.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_by_%(class)s',
        help_text='Usuario que creó el registro.'
    )

    # Usuario que actualizó el registro por última vez.
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_by_%(class)s',
        help_text='Usuario que actualizó por última vez el registro.'
    )

    # Usuario que eliminó lógicamente el registro.
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_by_%(class)s',
        help_text='Usuario que eliminó lógicamente el registro.'
    )

    # Usuario que restauró el registro eliminado.
    restored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restored_by_%(class)s',
        help_text='Usuario que restauró el registro eliminado.'
    )


    # Usuario que realizó el bloqueo.
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_users',
        help_text='Usuario que desactivó este usuario.'
    )


    # Usuario que realizó el desbloqueo.
    unblocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unblocked_users',
        help_text='Usuario que reactivó este usuario.'
    )
    # Autenticación por email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Manager
    objects = UserManager()

    def __str__(self):
        """
        Representación en texto del usuario.
        """
        return self.email


