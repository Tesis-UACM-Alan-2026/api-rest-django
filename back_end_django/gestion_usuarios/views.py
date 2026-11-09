#gestion_usuarios/views.py

import logging
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from core.utils import obtener_ip, auditar
from gestion_permisos.permissions import HasPermission
from gestion_usuarios.service import UsuarioService
from gestion_usuarios.VO.usuarioVO import UsuarioEntradaVO
from gestion_usuarios.serializers import (
    UsuarioCompletoSerializer,
    UsuarioParcialSerializer,
    UsuarioContrasenaSerializer,
    PasswordResetRequestSerializer,
    UsuarioRolesSerializer,
)
from gestion_usuarios.exceptions.usuarioExeptions import (
    UsuarioNoAutorizado_401,
    UsuarioProhibido_403,
    ErrorInternoServidor_500,
    UsuarioNoEncontrado_404,
    DatosInvalidos_400,
    ConflictoUsuario_409,
)

usuarioService = UsuarioService()

logger = logging.getLogger('gestion_usuarios')  # logs técnicos


class UsuarioViewSet(viewsets.ViewSet):
    """
    API para la gestión de Usuarios.
    """

    permisos_requeridos = {
        "list": "usuarios.ver",
        "retrieve": "usuarios.ver",
        "create": "usuarios.crear",
        "update": "usuarios.editar",
        "partial_update": "usuarios.editar",
        "destroy": "usuarios.eliminar",
        "activate": "usuarios.cambiar_estado",
        "deactivate": "usuarios.cambiar_estado",
        "restore": "usuarios.cambiar_estado",
        "verify_email": "usuarios.verificar_email",
        "asignar_roles": "usuarios.asignar_roles",
        "quitar_roles": "usuarios.asignar_roles",
    }

    def get_permissions(self):
        # Pública: cualquiera puede solicitar el restablecimiento
        if self.action == "request_password_reset":
            return [AllowAny()]

        # Solo exige estar autenticado (además se valida que sea el propio usuario)
        if self.action == "change_password":
            return [IsAuthenticated()]

        # Resto: autenticado + permiso por rol
        return [IsAuthenticated(), HasPermission()]

    ############################ LISTAR ############################
    @swagger_auto_schema(
        operation_summary="Obtener todos los usuarios",
        responses={
            200: "Éxito",
            401: "No autorizado",
            403: "Prohibido",
            500: "Error interno del servidor",
        },
    )
    def list(self, request, *args, **kwargs):
        """Devuelve la lista de todos los usuarios."""
        try:
            logger.debug("Solicitud para obtener todos los usuarios")
            usuarios_vo = usuarioService.listar_usuarios()
            serializer = UsuarioCompletoSerializer(usuarios_vo, many=True)
            logger.info(f"Lista de usuarios devuelta exitosamente. Total: {len(usuarios_vo)}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UsuarioNoAutorizado_401 as e:
            logger.warning(f"Intento no autorizado de obtener usuarios: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except UsuarioProhibido_403 as e:
            logger.warning(f"Intento prohibido de obtener usuarios: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ ACTIVAR ############################
    @swagger_auto_schema(
        operation_summary="Activar un usuario",
        responses={
            200: "Usuario activado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    @action(detail=True, methods=["patch"])
    def activate(self, request, pk=None):
        """Activa un usuario estableciendo el campo is_active en true."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando activar usuario con ID: {pk}")
            usuario_vo = usuarioService.activar_usuario(pk)
            logger.info(f"Usuario {pk} activado correctamente. IP: {ip}")
            auditar(ip, "ACTIVAR_USUARIO", request, id_afectado=pk)
            return Response(
                {
                    "mensaje": "Usuario activado correctamente",
                    "usuario": UsuarioParcialSerializer(usuario_vo).data,
                },
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Intento de activar usuario no encontrado: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"Intento de activar usuario con datos inválidos: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al activar usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ CONSULTAR ############################
    @swagger_auto_schema(
        operation_summary="Obtener un usuario por ID",
        responses={
            200: "Exito",
            401: "No Autorizado",
            403: "Prohibido",
            404: "Usuario no encontrado",
            500: "Error interno del servidor",
        },
    )
    def retrieve(self, request, pk=None):
        """Devuelve un usuario específico si existe."""
        try:
            logger.debug(f"Solicitud para obtener usuario con ID: {pk}")
            usuario_vo = usuarioService.obtener_usuario(pk)
            serializer = UsuarioCompletoSerializer(usuario_vo)
            logger.info(f"Usuario con ID {pk} devuelto exitosamente")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UsuarioNoAutorizado_401 as e:
            logger.warning(f"Intento no autorizado de obtener usuario con ID: {pk}")
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except UsuarioProhibido_403 as e:
            logger.warning(f"Intento prohibido de obtener usuario con ID: {pk}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Intento de obtener usuario no encontrado con ID: {pk}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ CREAR ############################
    @swagger_auto_schema(
        operation_summary="Crear un nuevo usuario",
        request_body=UsuarioCompletoSerializer,
        responses={
            201: "Usuario creado exitosamente",
            400: "Error en la validación",
            409: "Conflicto (email ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def create(self, request):
        """Crea un nuevo usuario con la información del cuerpo de la petición."""
        ip = obtener_ip(request)

        serializer = UsuarioCompletoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            entrada = UsuarioEntradaVO.desde_dict(serializer.validated_data)
            logger.debug(f"Intentando crear usuario: {entrada.email}")
            usuario_vo = usuarioService.crear_usuario(entrada)
            auditar(ip, "CREAR_USUARIO", request, nuevo_usuario=entrada.email)
            return Response(
                UsuarioCompletoSerializer(usuario_vo).data,
                status=status.HTTP_201_CREATED,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al crear usuario: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al crear usuario: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ ACTUALIZAR (PUT) ############################
    @swagger_auto_schema(
        operation_summary="Actualizar un usuario completamente",
        request_body=UsuarioCompletoSerializer,
        responses={
            200: "Usuario actualizado exitosamente",
            400: "Datos inválidos",
            404: "Usuario no encontrado",
            409: "Conflicto (email ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def update(self, request, pk=None):
        """Actualiza completamente un usuario especificado por su id."""
        ip = obtener_ip(request)

        serializer = UsuarioCompletoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if "password" in serializer.validated_data:
            return Response(
                {"error": "La contraseña no se modifica aquí. Use change-password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            logger.debug(f"Intentando actualizar usuario con ID: {pk}")
            entrada = UsuarioEntradaVO.desde_dict(serializer.validated_data)
            usuario_vo = usuarioService.actualizar_usuario(pk, entrada)
            auditar(ip, "ACTUALIZAR_USUARIO", request, id_afectado=pk)
            return Response(
                UsuarioCompletoSerializer(usuario_vo).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al actualizar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al actualizar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al actualizar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ ELIMINAR (lógico) ############################
    @swagger_auto_schema(
        operation_summary="Elimina un usuario (borrado lógico).",
        responses={
            200: "Usuario eliminado Correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def destroy(self, request, pk=None):
        """Desactiva el usuario (is_active = False) sin borrarlo físicamente."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando eliminar usuario con ID: {pk}")
            usuarioService.eliminar_usuario(pk)
            auditar(ip, "ELIMINAR_USUARIO", request, id_afectado=pk)
            return Response(
                {"mensaje": "Usuario eliminado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al eliminar usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ ACTUALIZAR (PATCH) ############################
    @swagger_auto_schema(
        operation_summary="Actualizar un usuario (parcial)",
        request_body=UsuarioParcialSerializer,
        responses={
            200: "Usuario actualizado parcialmente",
            400: "Datos inválidos",
            404: "Usuario no encontrado",
            409: "Conflicto (email ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def partial_update(self, request, pk=None):
        """Actualiza solo los campos proporcionados en el cuerpo de la petición."""
        ip = obtener_ip(request)

        serializer = UsuarioParcialSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.debug(f"Intentando actualizar parcialmente usuario con ID: {pk}")
            entrada = UsuarioEntradaVO.desde_dict(serializer.validated_data)
            usuario_vo = usuarioService.actualizar_usuario_parcial(pk, entrada)
            auditar(ip, "ACTUALIZAR_USUARIO_PARCIAL", request, id_afectado=pk)
            return Response(
                UsuarioParcialSerializer(usuario_vo).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al actualizar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al actualizar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al actualizar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ RESTAURAR ############################
    @swagger_auto_schema(
        operation_summary="Restaurar un usuario eliminado",
        responses={
            200: "Usuario restaurado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    @action(detail=True, methods=["patch"])
    def restore(self, request, pk=None):
        """Restaura un usuario eliminado lógicamente (is_active = True)."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando restaurar usuario con ID: {pk}")
            usuarioService.restaurar_usuario(pk)
            auditar(ip, "RESTAURAR_USUARIO", request, id_afectado=pk)
            return Response(
                {"mensaje": "Usuario restaurado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al restaurar usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ VERIFICAR EMAIL ############################
    @swagger_auto_schema(
        operation_summary="Verificar email del usuario",
        responses={
            200: "Email verificado exitosamente",
            401: "No autorizado",
            403: "Prohibido",
            400: "El email ya estaba verificado",
            404: "Usuario no encontrado",
            500: "Error interno del servidor",
        },
    )
    @action(detail=True, methods=["post"])
    def verify_email(self, request, pk=None):
        """Marca el email de un usuario como verificado."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando verificar email del usuario con ID: {pk}")
            usuarioService.verificar_email(pk)
            auditar(ip, "VERIFICAR_EMAIL", request, id_afectado=pk)
            return Response(
                {"mensaje": "Email verificado exitosamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"Email ya verificado para usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # No se expone el detalle interno al cliente
            logger.error(f"Error interno al verificar email del usuario {pk}: {str(e)}")
            return Response(
                {"error": "Error interno del servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    ############################ DESACTIVAR ############################
    @swagger_auto_schema(
        operation_summary="Desactivar un usuario",
        responses={
            200: "Usuario desactivado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    @action(detail=True, methods=["patch"])
    def deactivate(self, request, pk=None):
        """Desactiva un usuario estableciendo el campo is_active en false."""
        ip = obtener_ip(request)
        try:
            logger.debug(f"Intentando desactivar usuario con ID: {pk}")
            usuarioService.desactivar_usuario(pk)
            auditar(ip, "DESACTIVAR_USUARIO", request, id_afectado=pk)
            return Response(
                {"mensaje": "Usuario desactivado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al desactivar usuario con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al desactivar usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ CAMBIAR CONTRASEÑA ############################
    @swagger_auto_schema(
        operation_summary="Cambiar contraseña del usuario",
        request_body=UsuarioContrasenaSerializer,
        responses={
            200: "Contraseña actualizada correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    @action(detail=True, methods=["post"], url_path="change-password")
    def change_password(self, request, pk=None):
        """Cambia la contraseña proporcionando la actual y la nueva."""
        ip = obtener_ip(request)

        # Cada usuario solo puede cambiar SU propia contraseña
        if str(pk) != str(request.user.pk):
            return Response(
                {"error": "Solo puede cambiar su propia contraseña."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UsuarioContrasenaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.debug(f"Intentando cambiar contraseña para usuario con ID: {pk}")
            usuarioService.cambiar_contrasena(
                pk,
                serializer.validated_data["current_password"],
                serializer.validated_data["new_password"],
                serializer.validated_data["confirm_password"],
            )
            auditar(ip, "CAMBIAR_CONTRASENA", request, id_afectado=pk)
            return Response(
                {"mensaje": "Contraseña actualizada correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            logger.warning(f"Error de validación al cambiar contraseña para usuario con ID {pk}: {str(e)}")
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al cambiar contraseña del usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ SOLICITAR RESET ############################
    @swagger_auto_schema(
        operation_summary="Solicitar restablecimiento de contraseña",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: "Se ha enviado un enlace de restablecimiento a tu correo",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    @action(detail=False, methods=["post"], url_path="request-password-reset")
    def request_password_reset(self, request):
        """Solicita un restablecimiento de contraseña (genera token de 1 hora)."""
        ip = obtener_ip(request)

        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            logger.debug(f"Solicitud de restablecimiento de contraseña para email: {email}")
            # El token NO se devuelve al cliente; aquí debe enviarse por correo.
            usuarioService.solicitar_reset_password(email)
            auditar(ip, "REQUEST_PASSWORD_RESET", request, email_afectado=email)
            return Response(
                {"mensaje": "Se ha enviado un enlace de restablecimiento a tu correo"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado para email {email}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al solicitar restablecimiento para {email}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ############################ ROLES DEL USUARIO ############################
    @swagger_auto_schema(
        operation_summary="Asignar roles a un usuario",
        operation_description="Agrega los roles indicados. Los ya asignados se ignoran.",
        request_body=UsuarioRolesSerializer,
        responses={
            200: UsuarioCompletoSerializer(),
            400: "Datos inválidos o roles inexistentes",
            404: "Usuario no encontrado",
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="asignar-roles",
    )
    def asignar_roles(self, request, pk=None):
        """Asigna uno o más roles a un usuario (solo administradores)."""
        ip = obtener_ip(request)

        serializer = UsuarioRolesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            roles_ids = serializer.validated_data["roles"]
            logger.debug(f"Intentando asignar roles {roles_ids} al usuario {pk}")
            usuario_vo = usuarioService.asignar_roles(pk, roles_ids)
            auditar(
                ip, "ASIGNAR_ROLES_USUARIO", request,
                id_afectado=pk, roles=sorted(set(roles_ids))
            )
            return Response(
                UsuarioCompletoSerializer(usuario_vo).data,
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"Error al asignar roles al usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al asignar roles al usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Quitar roles a un usuario",
        operation_description="Quita los roles indicados. Los no asignados se ignoran.",
        request_body=UsuarioRolesSerializer,
        responses={
            200: UsuarioCompletoSerializer(),
            400: "Datos inválidos",
            404: "Usuario no encontrado",
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="quitar-roles",
    )
    def quitar_roles(self, request, pk=None):
        """Quita uno o más roles a un usuario (solo administradores)."""
        ip = obtener_ip(request)

        serializer = UsuarioRolesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            roles_ids = serializer.validated_data["roles"]
            logger.debug(f"Intentando quitar roles {roles_ids} al usuario {pk}")
            usuario_vo = usuarioService.quitar_roles(pk, roles_ids)
            auditar(
                ip, "QUITAR_ROLES_USUARIO", request,
                id_afectado=pk, roles=sorted(set(roles_ids))
            )
            return Response(
                UsuarioCompletoSerializer(usuario_vo).data,
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al quitar roles al usuario {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)