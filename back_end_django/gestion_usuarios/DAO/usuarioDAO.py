###CODIGO 15#############
from gestion_usuarios.models import Usuario
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from datetime import timedelta
from gestion_usuarios.serializers import UsuarioParcialSerializer, UsuarioContrasenaSerializer
from gestion_usuarios.exceptions.usuarioExeptions import (
    DatosInvalidos_400,
    UsuarioNoEncontrado_404,
    ConflictoUsuario_409,
    ErrorInternoServidor_500,
    UsuarioNoAutorizado_401,
    UsuarioProhibido_403,
)
from django.db.utils import IntegrityError, DatabaseError
import uuid


class UsuarioDAO:
    """
    Data Access Object (DAO) para la gestión de usuarios en la base de datos.
    Proporciona métodos para realizar operaciones CRUD sobre el modelo Usuario.
    """
###################CODIGO 18########################
    @staticmethod
    def obtener_todos():
        return Usuario.objects.all()
##################CODIGO 20############
    @staticmethod
    def obtener_usuario_por_id(usuario_id):
        try:
            usuario = Usuario.objects.filter(id=usuario_id).first()

            if usuario is None:
                raise UsuarioNoEncontrado_404(
                    "El usuario no existe."
                )

            return usuario

        except UsuarioNoEncontrado_404:
            raise
        except DatabaseError:
            raise ErrorInternoServidor_500()

    @staticmethod
    def activar_usuario(pk):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        # este if es redundante porque obtener_usuario_por_id ya lanza excepción, pero lo dejo
        if not usuario:
            raise UsuarioNoEncontrado_404()  # <-- fatal corregido (faltaban paréntesis)

        if usuario.is_active:
            raise DatosInvalidos_400("El usuario ya estaba activo")

        usuario.is_active = True
        usuario.save()
        return usuario
  #######################CODIGO 22###############################################
    @staticmethod
    def crear_usuario(
            email: str,
            password: str,
            first_name: str,
            last_name: str,
    ):
        """
        Crea un nuevo usuario con validaciones.
        """

        # Validar correo electrónico
        try:
            validate_email(email)
        except ValidationError:
            raise DatosInvalidos_400("El correo electrónico no es válido.")

        # Validar campos obligatorios
        if not password:
            raise DatosInvalidos_400("La contraseña es obligatoria.")

        if not first_name or not last_name:
            raise DatosInvalidos_400(
                "El nombre y apellido son obligatorios."
            )

        # Validar si el correo ya existe
        if Usuario.objects.filter(email=email).exists():
            raise ConflictoUsuario_409(
                "El correo electrónico ya está registrado."
            )

        try:
            usuario = Usuario(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )

            usuario.set_password(password)
            usuario.save()

            return usuario

        except IntegrityError:
            raise ConflictoUsuario_409(
                "El correo electrónico ya está registrado."
            )

        except DatabaseError:
            raise ErrorInternoServidor_500()
    ##########Codigo 26 ########################################################

    @staticmethod
    def actualizar_usuario(usuario_id, datos):
        try:
            usuario = UsuarioDAO.obtener_usuario_por_id(usuario_id)

            campos_permitidos = [
                "email",
                "first_name",
                "last_name",
            ]

            for campo, valor in datos.items():
                if campo not in campos_permitidos:
                    raise DatosInvalidos_400(
                        f"El campo '{campo}' no está permitido."
                    )

                setattr(usuario, campo, valor)

            if "email" in datos:
                try:
                    validate_email(usuario.email)
                except ValidationError:
                    raise DatosInvalidos_400(
                        "El correo electrónico no es válido."
                    )

                existe = Usuario.objects.filter(
                    email=usuario.email
                ).exclude(id=usuario.id).exists()

                if existe:
                    raise ConflictoUsuario_409(
                        "El correo electrónico ya está registrado."
                    )

            usuario.save()
            return usuario

        except (
                UsuarioNoEncontrado_404,
                DatosInvalidos_400,
                ConflictoUsuario_409,
        ):
            raise
        except IntegrityError:
            raise ConflictoUsuario_409(
                "No fue posible actualizar el usuario por un conflicto de datos."
            )
        except DatabaseError:
            raise ErrorInternoServidor_500()
       #############Codigo 28#######################################################
    @staticmethod
    def eliminar_usuario(usuario_id):
        try:
            usuario = UsuarioDAO.obtener_usuario_por_id(usuario_id)

            usuario.is_active = False
            usuario.save(update_fields=["is_active"])

            return usuario

        except UsuarioNoEncontrado_404:
            raise
        except DatabaseError:
            raise ErrorInternoServidor_500()
###################Codigo 30########################################################
    CAMPOS_OPCIONALES = [
        "username",
        "password",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_superuser",
        "profile_picture",
        "nationality",
        "occupation",
        "date_of_birth",
        "contact_phone_number",
        "gender",
        "address",
        "address_number",
        "address_interior_number",
        "address_complement",
        "address_neighborhood",
        "address_zip_code",
        "address_city",
        "address_state",
        "role",
    ]
    @staticmethod
    def actualizar_usuario_parcial(pk, **datos):
        """
        Actualiza los datos de un usuario existente de forma parcial.

        :param pk: UUID del usuario a actualizar.
        :param datos: Diccionario con los campos a modificar.
        :return: Instancia del usuario actualizado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")

        # Verificación de username y email duplicados
        if "username" in datos and datos["username"] != usuario.username:
            if Usuario.objects.filter(username=datos["username"]).exclude(id=pk).exists():
                raise ConflictoUsuario_409("El nombre de usuario ya está registrado.")

        if "email" in datos and datos["email"] != usuario.email:
            if Usuario.objects.filter(email=datos["email"]).exclude(id=pk).exists():
                raise ConflictoUsuario_409("El correo electrónico ya está registrado.")

        # Actualización de campos permitidos
        for campo, valor in datos.items():
            if campo in UsuarioDAO.CAMPOS_OPCIONALES:

                if campo == "password":
                    usuario.password = make_password(valor)
                else:
                    setattr(usuario, campo, valor)

        # Guardar cambios
        usuario.save()

        return usuario 
    ##############Codigo 32########################################################
    @staticmethod
    def restaurar_usuario(usuario_id):
        try:
            usuario = UsuarioDAO.obtener_usuario_por_id(usuario_id)

            usuario.is_active = True
            usuario.save(update_fields=["is_active"])

            return usuario

        except UsuarioNoEncontrado_404:
            raise
        except DatabaseError:
            raise ErrorInternoServidor_500()
##############Codigo 34#######################################################
    @staticmethod
    def verificar_email(pk):
        """
        Verifica el email del usuario especificado por su ID.

        :param pk: ID del usuario a verificar.
        :return: Instancia del usuario con el email verificado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        # Este if es redundante porque obtener_usuario_por_id ya lanza UsuarioNoEncontrado_404()
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")

        if usuario.email_verified:
            raise DatosInvalidos_400("El email ya estaba verificado.")

        usuario.email_verified = True
        usuario.email_verified_at = timezone.now()
        usuario.save()
        return usuario  
###########Codigo 36########################################################  
    @staticmethod
    def desactivar_usuario(pk):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        # Redundante, porque obtener_usuario_por_id ya lanza UsuarioNoEncontrado_404()
        if not usuario:
            raise UsuarioNoEncontrado_404("Usuario no encontrado.")

        if usuario.is_active:
            usuario.is_active = False
            usuario.save()
            return usuario
        else:
            raise DatosInvalidos_400("El usuario ya estaba desactivado.") 
##############Codigo 38########################################################
    @staticmethod
    def actualizar_contrasena(pk, current_password, new_password, confirm_password):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        # Redundante, porque obtener_usuario_por_id ya lanza UsuarioNoEncontrado_404()
        if not usuario:
            raise UsuarioNoEncontrado_404("El usuario no existe.")

        # Tu modelo Usuario NO tiene check_password(); usa check_password de Django
        if not check_password(current_password, usuario.password):
            raise ValidationError("La contraseña actual no es correcta.")

        serializer = UsuarioContrasenaSerializer(
            data={
                "current_password": current_password,
                "new_password": new_password,
                "confirm_password": confirm_password,
            }
        )

        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        usuario.password = make_password(new_password)
        usuario.save()

        return usuario 
###########Codigo 41#######################################################
    @staticmethod
    def reset_password(token, new_password):
        """Restablece la contraseña usando el token."""
        usuario = Usuario.objects.filter(reset_password_token=token).first()
        if not usuario:
            raise DatosInvalidos_400("Token inválido.")

        if not usuario.reset_password_expires_at or usuario.reset_password_expires_at < timezone.now():
            raise DatosInvalidos_400("Token inválido o expirado.")

        # Restablece la contraseña y borra el token
        usuario.password = make_password(new_password)
        usuario.reset_password_token = None
        usuario.reset_password_expires_at = None
        usuario.save()
        return usuario  
    @staticmethod
    def reset_password_request(email):
        """
        Genera un token de recuperación de contraseña.
        """

        usuario = Usuario.objects.filter(
            email=email,
            is_deleted=False
        ).first()

        if not usuario:
            raise UsuarioNoEncontrado_404()

        usuario.reset_password_token = uuid.uuid4()
        usuario.reset_password_expires_at = (
            timezone.now() + timedelta(hours=1)
        )

        usuario.save()

        return {
            "token": str(usuario.reset_password_token),
            "expires_at": usuario.reset_password_expires_at,
        }