from rest_framework import serializers
from ..models import User
from ..choices import assign_user_to_role, RoleChoices
from django.contrib.auth.models import Permission
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.tokens  import TokenError
from django.contrib.auth import authenticate
import time
from django.utils.timezone import now

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para obtener el par de tokens (access y refresh) en el login.

    Este serializer extiende el serializer base de SimpleJWT (`TokenObtainPairSerializer`)
    y agrega información del usuario al payload de respuesta, como su ID, correo...

    Métodos sobrescritos:
        - get_user_instance: valida las credenciales (email y contraseña) para verificar la eliminacion logica.
        - validate: revalida las credenciales y construye la respuesta con información adicional.
    """

    def get_user_instance(self, attrs):
        """
        Obtiene la instancia de usuario autenticada a partir de las credenciales proporcionadas.
        Args:
            attrs (dict): Diccionario que contiene las credenciales del usuario ('email' y 'password').
        Returns:
            User: Objeto de usuario autenticado.
        Raises:
            ValidationError: Si faltan el email o la contraseña en la solicitud.
            AuthenticationFailed: Si las credenciales proporcionadas son inválidas.
        Buenas prácticas:
            - Validación de campos requeridos.
            - Uso de autenticación segura con el contexto del request.
            - Manejo explícito de errores de validación y autenticación.
        """
        
        email = attrs.get("email", "")
        password = attrs.get("password", "")
        if not email or not password:
            raise ValidationError
            
        user = authenticate(request=self.context.get('request'),username=email,password=password)
        if user is None:
            raise AuthenticationFailed
        return user
    
    def validate(self, attrs):
        """
        Valida las credenciales del usuario y enriquece la respuesta con datos adicionales (IP, roles, permisos).
        Args:
            attrs (dict): Diccionario con las credenciales del usuario ('email' y 'password').
        Returns:
            dict: Datos del usuario autenticado junto con sus roles y permisos.
        Raises:
            AuthenticationFailed: Si las credenciales son inválidas.
            ValidationError: Si ocurre un error de validación en los datos.
            Exception: Cualquier otro error inesperado durante la validación.
        Buenas prácticas:
            - Registro de la IP y la fecha/hora del último inicio de sesión.
            - Enriquecimiento de la respuesta con roles y permisos.
            - Manejo explícito de errores con mensajes claros.
        """
        
        try:
            #se verifica que el usuario exista y que este activo
            data = super().validate(attrs)

            request = self.context["request"]
            user = self.user

            # Guardar la IP del usuario
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")

            # Registrar login exitoso
            user.last_login_IP = ip
            user.last_login = now()
            user.save(update_fields=["last_login_IP", "last_login"])
            
            # Obtener todos los permisos como strings: "app_label.codename"
            permission_strings = self.user.get_all_permissions()

            # Separar codenames
            codenames = [perm.split('.')[-1] for perm in permission_strings]
            
            #Obtener los role del usuario
            role_enum = RoleChoices(self.user.role) if self.user.role else None


            # Buscar los objetos Permission por codename
            permissions_qs = Permission.objects.filter(codename__in=codenames)
            data['user'] = {
                "userId": getattr(self.user, 'user_id', None),
                "name": getattr(self.user, 'name', None),
                "firstLastname": getattr(self.user, 'first_lastname', None),
                "email": getattr(self.user, 'email', None),
                "emailVerified": getattr(self.user, 'email_verified', None),
                "isSuperuser": getattr(self.user, 'is_superuser', None),
                "isStaff": getattr(self.user, 'is_staff', None),
                "isActive": getattr(self.user, 'is_active', None),
                "roles": [
                    {
                        "roleId": getattr(role_enum, 'roleId', None),
                        "name": getattr(role_enum, 'name', None),
                        "label": getattr(role_enum, 'label', None),
                    }
                ] if role_enum else [],
                "permissions": [
                    {
                        "permissionId": perm.id,
                        "name": perm.codename,
                        "label": perm.name,
                    }
                    for perm in permissions_qs
                ]
            }
            return data
        except AuthenticationFailed as e:
            raise AuthenticationFailed(str(e)) 
        except ValidationError as e:
            raise ValidationError(str(e))

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Serializer personalizado para refrescar el token de acceso (access) usando un token de actualización (refresh).

    Este serializer extiende el serializer base de SimpleJWT (`TokenRefreshSerializer`)
    y captura de forma controlada los errores comunes que se producen cuando el token es inválido
    o ha expirado, devolviendo un mensaje de error amigable.

    Métodos sobrescritos:
        - validate: procesa el token de refresco y devuelve un nuevo token de acceso.
    """
    def validate(self, attrs):
        """
        Valida el token de refresh asegurándose de que sea válido, esté bien formado y no haya expirado.
        Args:
            attrs (dict): Diccionario que contiene el token de refresh a validar.
        Returns:
            dict: Datos validados del token si es correcto.
        Raises:
            AuthenticationFailed: Si el token es inválido, expirado o mal formado.
            ValidationError: Si ocurre un error de validación específico.
            Exception: Cualquier otro error inesperado durante la validación.
        Buenas prácticas:
            - Manejo explícito y detallado de errores.
            - Uso del método validate del serializer base para centralizar la lógica de validación.
            - Retorno controlado de mensajes de error claros para el cliente.
        """
        try:
            # verifica que token sea valido y no este expirado
            data = super().validate(attrs)
            return data
        except AuthenticationFailed as e:
            raise AuthenticationFailed(str(e))
        except TokenError as e:
            raise TokenError(str(e))
        except ValidationError as e:
            raise ValidationError(str(e))

