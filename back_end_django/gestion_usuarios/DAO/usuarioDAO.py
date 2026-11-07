###CODIGO 15#############
import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.utils import IntegrityError, DatabaseError
from django.utils import timezone

from gestion_usuarios.models import Usuario
from gestion_permisos.models import Rol
from gestion_usuarios.exceptions.usuarioExeptions import (
    DatosInvalidos_400,
    UsuarioNoEncontrado_404,
    ConflictoUsuario_409,
    ErrorInternoServidor_500,
)


class UsuarioDAO:
    """
    Data Access Object (DAO) para la gestión de usuarios en la base de datos.
    Proporciona métodos para realizar operaciones CRUD sobre el modelo Usuario.
    """

    # Campos del perfil que se pueden modificar (PUT / PATCH).
    # La contraseña, is_active, is_staff, etc. NUNCA se modifican por aquí.
    CAMPOS_EDITABLES = ("email", "first_name", "last_name")

    LONGITUD_MINIMA_PASSWORD = 8
    HORAS_VALIDEZ_TOKEN = 1

    # ------------------------------------------------------------------
    # Validaciones internas
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_email(email):
        try:
            validate_email(email)
        except ValidationError:
            raise DatosInvalidos_400("El correo electrónico no es válido.")

    @staticmethod
    def _validar_password(password):
        if not password:
            raise DatosInvalidos_400("La contraseña es obligatoria.")

        if len(password) < UsuarioDAO.LONGITUD_MINIMA_PASSWORD:
            raise DatosInvalidos_400(
                "La contraseña debe contener al menos "
                f"{UsuarioDAO.LONGITUD_MINIMA_PASSWORD} caracteres."
            )

    ###################CODIGO 18########################
    @staticmethod
    def obtener_todos():
        return Usuario.objects.prefetch_related("roles").order_by("date_joined")

    ##################CODIGO 20############
    @staticmethod
    def obtener_usuario_por_id(usuario_id):
        try:
            usuario = Usuario.objects.prefetch_related("roles").filter(id=usuario_id).first()

            if usuario is None:
                raise UsuarioNoEncontrado_404("El usuario no existe.")

            return usuario

        except UsuarioNoEncontrado_404:
            raise
        except (ValidationError, ValueError, TypeError):
            # El id recibido no es un UUID válido
            raise UsuarioNoEncontrado_404("El usuario no existe.")
        except DatabaseError:
            raise ErrorInternoServidor_500()

    @staticmethod
    def activar_usuario(pk):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        if usuario.is_active:
            raise DatosInvalidos_400("El usuario ya estaba activo")

        try:
            usuario.is_active = True
            usuario.save(update_fields=["is_active"])
            return usuario
        except DatabaseError:
            raise ErrorInternoServidor_500()

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
        UsuarioDAO._validar_email(email)
        UsuarioDAO._validar_password(password)

        if not first_name or not last_name:
            raise DatosInvalidos_400(
                "El nombre y apellido son obligatorios."
            )

        try:
            if Usuario.objects.filter(email__iexact=email).exists():
                raise ConflictoUsuario_409(
                    "El correo electrónico ya está registrado."
                )

            usuario = Usuario(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )

            usuario.set_password(password)
            usuario.save()

            return usuario

        except ConflictoUsuario_409:
            raise
        except IntegrityError:
            raise ConflictoUsuario_409(
                "El correo electrónico ya está registrado."
            )
        except DatabaseError:
            raise ErrorInternoServidor_500()

    ##########Codigo 26 ########################################################
    @staticmethod
    def actualizar_usuario(usuario_id, datos):
        """
        Actualiza los campos del perfil (email, first_name, last_name).

        :param usuario_id: UUID del usuario a actualizar.
        :param datos: dict con los campos a modificar.
        :return: Instancia del usuario actualizado.
        """
        try:
            usuario = UsuarioDAO.obtener_usuario_por_id(usuario_id)

            for campo in datos:
                if campo not in UsuarioDAO.CAMPOS_EDITABLES:
                    raise DatosInvalidos_400(
                        f"El campo '{campo}' no está permitido."
                    )

            if "email" in datos:
                UsuarioDAO._validar_email(datos["email"])

                existe = Usuario.objects.filter(
                    email__iexact=datos["email"]
                ).exclude(id=usuario.id).exists()

                if existe:
                    raise ConflictoUsuario_409(
                        "El correo electrónico ya está registrado."
                    )

            for campo, valor in datos.items():
                setattr(usuario, campo, valor)

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
        """Borrado lógico: marca al usuario como inactivo."""
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
    @staticmethod
    def actualizar_usuario_parcial(pk, **datos):
        """
        Actualiza de forma parcial los campos del perfil.

        :param pk: UUID del usuario a actualizar.
        :param datos: Campos a modificar (solo email, first_name, last_name).
        :return: Instancia del usuario actualizado.
        """
        return UsuarioDAO.actualizar_usuario(pk, datos)

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
        Requiere los campos email_verified y email_verified_at en el modelo.

        :param pk: ID del usuario a verificar.
        :return: Instancia del usuario con el email verificado.
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        if usuario.email_verified:
            raise DatosInvalidos_400("El email ya estaba verificado.")

        try:
            usuario.email_verified = True
            usuario.email_verified_at = timezone.now()
            usuario.save(update_fields=["email_verified", "email_verified_at"])
            return usuario
        except DatabaseError:
            raise ErrorInternoServidor_500()

    ###########Codigo 36########################################################
    @staticmethod
    def desactivar_usuario(pk):
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        if not usuario.is_active:
            raise DatosInvalidos_400("El usuario ya estaba desactivado.")

        try:
            usuario.is_active = False
            usuario.save(update_fields=["is_active"])
            return usuario
        except DatabaseError:
            raise ErrorInternoServidor_500()

    ##############Codigo 38########################################################
    @staticmethod
    def actualizar_contrasena(pk, current_password, new_password, confirm_password):
        """
        Cambia la contraseña verificando la actual.
        Lanza django.core.exceptions.ValidationError (la vista la traduce a 400).
        """
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        if not usuario.check_password(current_password):
            raise ValidationError("La contraseña actual no es correcta.")

        if len(new_password) < UsuarioDAO.LONGITUD_MINIMA_PASSWORD:
            raise ValidationError(
                "La nueva contraseña debe contener al menos "
                f"{UsuarioDAO.LONGITUD_MINIMA_PASSWORD} caracteres."
            )

        if new_password != confirm_password:
            raise ValidationError("Las contraseñas no coinciden.")

        try:
            usuario.set_password(new_password)
            usuario.save(update_fields=["password"])
            return usuario
        except DatabaseError:
            raise ErrorInternoServidor_500()

    ###########Codigo 41#######################################################
    @staticmethod
    def reset_password(token, new_password):
        """Restablece la contraseña usando el token."""
        UsuarioDAO._validar_password(new_password)

        try:
            usuario = Usuario.objects.filter(reset_password_token=token).first()
        except (ValidationError, ValueError, TypeError):
            # El token no tiene formato UUID
            raise DatosInvalidos_400("Token inválido.")
        except DatabaseError:
            raise ErrorInternoServidor_500()

        if not usuario:
            raise DatosInvalidos_400("Token inválido.")

        if (
                not usuario.reset_password_expires_at
                or usuario.reset_password_expires_at < timezone.now()
        ):
            raise DatosInvalidos_400("Token inválido o expirado.")

        try:
            # Restablece la contraseña e invalida el token (uso único)
            usuario.set_password(new_password)
            usuario.reset_password_token = None
            usuario.reset_password_expires_at = None
            usuario.save(
                update_fields=[
                    "password",
                    "reset_password_token",
                    "reset_password_expires_at",
                ]
            )
            return usuario
        except DatabaseError:
            raise ErrorInternoServidor_500()

    @staticmethod
    def reset_password_request(email):
        """
        Genera un token de recuperación de contraseña (válido 1 hora).
        """
        try:
            usuario = Usuario.objects.filter(
                email__iexact=email,
                is_active=True
            ).first()

            if not usuario:
                raise UsuarioNoEncontrado_404()

            usuario.reset_password_token = uuid.uuid4()
            usuario.reset_password_expires_at = (
                    timezone.now() + timedelta(hours=UsuarioDAO.HORAS_VALIDEZ_TOKEN)
            )
            usuario.save(
                update_fields=[
                    "reset_password_token",
                    "reset_password_expires_at",
                ]
            )

            return {
                "token": str(usuario.reset_password_token),
                "expires_at": usuario.reset_password_expires_at,
            }

        except UsuarioNoEncontrado_404:
            raise
        except DatabaseError:
            raise ErrorInternoServidor_500()

    # ------------------------------------------------------------------
    # Roles del usuario
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def asignar_roles(pk, roles_ids):
        """Agrega roles a un usuario (los ya asignados se ignoran)."""
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)
        ids = set(roles_ids)

        try:
            roles = list(Rol.objects.filter(id__in=ids))
            inexistentes = ids - {r.id for r in roles}

            if inexistentes:
                raise DatosInvalidos_400(
                    f"Los siguientes roles no existen: {sorted(inexistentes)}"
                )

            usuario.roles.add(*roles)

        except DatosInvalidos_400:
            raise
        except DatabaseError:
            raise ErrorInternoServidor_500()

        # Se vuelve a consultar para devolver los roles actualizados
        return UsuarioDAO.obtener_usuario_por_id(pk)

    @staticmethod
    @transaction.atomic
    def quitar_roles(pk, roles_ids):
        """Quita roles de un usuario (los no asignados se ignoran)."""
        usuario = UsuarioDAO.obtener_usuario_por_id(pk)

        try:
            usuario.roles.remove(*set(roles_ids))
        except DatabaseError:
            raise ErrorInternoServidor_500()

        return UsuarioDAO.obtener_usuario_por_id(pk)