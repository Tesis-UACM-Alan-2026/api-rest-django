#######CODIGO 17############
import logging 
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_yasg.utils import swagger_auto_schema

from gestion_usuarios.DAO.usuarioDAO import UsuarioDAO
from gestion_usuarios.serializers import (
    UsuarioCompletoSerializer,
    UsuarioParcialSerializer,
    UsuarioContrasenaSerializer,
    PasswordResetRequestSerializer,
)
from gestion_usuarios.exceptions.usuarioExeptions import (
    UsuarioNoAutorizado_401,
    UsuarioProhibido_403,
    ErrorInternoServidor_500,
    UsuarioNoEncontrado_404,
    DatosInvalidos_400,
    ConflictoUsuario_409,
)

logger = logging.getLogger('gestion_usuarios') #logs técnicos
logger_auditoria = logging.getLogger('auditoria') #logs de auditoría

def obtener_ip(request): #Nos permite obtener la IP real del cliente, incluso si está detrás de un proxy o balanceador de carga.
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'IP desconocida')


class UsuarioViewSet(viewsets.ViewSet):
    """
    API para la gestión de Usuarios.
    """

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
        """
        Devuelve una lista de todos los usuarios con soporte para
        paginación, ordenamiento y filtrado de acuerdo a los campos
        de la tabla.
        """
        try:
            logger.debug("Solicitud para obtener todos los usuarios") #NUEVO
            usuarios = UsuarioDAO.obtener_todos()
            serializer = UsuarioCompletoSerializer(
                usuarios,
                many=True
            )
            logger.info(f"Lista de usuarios devuelta exitosamente. Total: {len(usuarios)}") #NUEVO
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        except UsuarioNoAutorizado_401 as e:
            logger.warning(f"Intento no autorizado de obtener usuarios: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except UsuarioProhibido_403 as e:
            logger.warning(f"Intento prohibido de obtener usuarios: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
############################Codigo 19########################################################
    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Activar un usuario",
        responses={
            200: "Usuario activado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def activate(self, request, pk=None):
        """Activa un usuario estableciendo el campo is_active en true."""
        ip = obtener_ip(request)
        try:
            logger.info(f"Usuario activado correctamente. IP: {ip}") #NUEVO
            usuario = UsuarioDAO.activar_usuario(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTIVAR_USUARIO] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )
            return Response(
                {
                    "mensaje": "Usuario activado correctamente",
                    "usuario": UsuarioParcialSerializer(usuario).data,
                },
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Intento de activar usuario no encontrado: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except DatosInvalidos_400 as e:
            logger.warning(f"Intento de activar usuario con datos inválidos: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)    
###############CODIGO 21########################################################
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
            logger.debug(f"Solicitud para obtener usuario con ID: {pk}") #NUEVO
            usuario = UsuarioDAO.obtener_usuario_por_id(pk)
            serializer = UsuarioCompletoSerializer(usuario)
            logger.info(f"Usuario con ID {pk} devuelto exitosamente") #NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UsuarioNoAutorizado_401 as e:
            logger.warning(f"Intento no autorizado de obtener usuario con ID: {pk}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except UsuarioProhibido_403 as e:
            logger.warning(f"Intento prohibido de obtener usuario con ID: {pk}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Intento de obtener usuario no encontrado con ID: {pk}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
############CUADRO 23########################################################
    @swagger_auto_schema(
        operation_summary="Crear un nuevo usuario",
        request_body=UsuarioParcialSerializer,
        responses={
            201: "Usuario creado exitosamente",
            400: "Error en la validación",
            409: "Conflicto (nombre de usuario o email ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def create(self, request):
        """Crea un nuevo usuario con la información proporcionada en el cuerpo de la petición."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger .debug(f" Intentando crear usuario : { request .data.get(' username ')}") #NUEVO
            usuario_dto = UsuarioDAO.crear_usuario(**request.data)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:CREAR_USUARIO] "
                f"[ realizado_por :{ request .user }]"
                f"[ nuevo_usuario :{ request .data.get(' username ')}]"
            )
            return Response(
                UsuarioCompletoSerializer(usuario_dto).data,
                status=status.HTTP_201_CREATED,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al crear usuario: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al crear usuario: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    ############Codigo 25########################################################
    @swagger_auto_schema(
        operation_summary="Actualizar un usuario completamente",
        request_body=UsuarioCompletoSerializer,
        responses={
            200: "Usuario actualizado exitosamente",
            400: "Datos inválidos",
            404: "Usuario no encontrado",
            409: "Conflicto (nombre de usuario o email ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def update(self, request, pk=None):
        """Actualiza completamente un usuario especificado por su id"""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando actualizar usuario con ID: {pk}") #NUEVO
            usuarioDTO = UsuarioDAO.actualizar_usuario(pk, **request.data)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_USUARIO] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )
            return Response(
                UsuarioCompletoSerializer(usuarioDTO).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al actualizar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al actualizar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al actualizar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#########Codigo 27 ########################################################
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
        """Marca el usuario como eliminado sin borrarlo físicamente de la base de datos. Esto se realiza actualizando los campos is_deleted y deleted_at."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando eliminar usuario con ID: {pk}") #NUEVO
            UsuarioDAO.eliminar_usuario(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ELIMINAR_USUARIO] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )
            return Response(
                {"mensaje": "Usuario eliminado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Error de validación al eliminar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#########codigo 29########################################################
    @swagger_auto_schema(
        operation_summary="Actualizar un usuario (parcial)",
        request_body=UsuarioParcialSerializer,
        responses={
            200: "Usuario actualizado parcialmente",
            400: "Datos inválidos",
            404: "Usuario no encontrado",
            409: "Conflicto (nombre de usuario o email ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def partial_update(self, request, pk=None):
        """Actualiza parcialmente un usuario especificado por su id. Solo se actualizan los campos proporcionados en el cuerpo de la petición."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando actualizar usuario con ID: {pk}") #NUEVO
            usuarioDTO = UsuarioDAO.actualizar_usuario_parcial(pk, **request.data)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_USUARIO] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )
            return Response(
                UsuarioParcialSerializer(usuarioDTO).data,
                status=status.HTTP_200_OK,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al actualizar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoUsuario_409 as e:
            logger.warning(f"Conflicto al actualizar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno del servidor al actualizar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
        ############Codigo 31########################################################
    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Restaurar un usuario eliminado",
        responses={
            200: "Usuario restaurado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def restore(self, request, pk=None):
        """Restaura un usuario que había sido marcado como eliminado lógicamente. Esto se realiza actualizando los campos is_deleted y deleted_at."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando restaurar usuario con ID: {pk}") #NUEVO
            usuario = UsuarioDAO.restaurar_usuario(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:RESTAURAR_USUARIO] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )
            return Response(
                {"mensaje": "Usuario restaurado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Error de validación al restaurar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)   
########Codigo 33########################################################
    @action(detail=True, methods=["post"])
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
    def verify_email(self, request, pk=None):
        """
        Marca el email de un usuario como verificado y actualiza
        la fecha de verificación en el campo email_verified_at.
        """
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando verificar email del usuario con ID: {pk}") #NUEVO
            UsuarioDAO.verificar_email(pk)

            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:VERIFICAR_EMAIL] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )

            return Response(
                {"mensaje": "Email verificado exitosamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Email ya verificado para usuario con ID {pk}: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValueError as e:
            logger.warning(f"Error de validación al verificar email para usuario con ID {pk}: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Error interno del servidor al verificar email para usuario con ID {pk}: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )     
####################Codigo 35########################################################
    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Desactivar un usuario",
        responses={
            200: "Usuario eliminado Correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def deactivate(self, request, pk=None):
        """Desactiva un usuario estableciendo el campo is_active en false."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando desactivar usuario con ID: {pk}") #NUEVO
            UsuarioDAO.desactivar_usuario(pk)

            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:DESACTIVAR_USUARIO] "
                f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
            )

            return Response(
                {"mensaje": "Usuario eliminado correctamente"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Error de validación al desactivar usuario con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)   
#############Codigo 37########################################################|
    @action(detail=True, methods=["post"])
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
    def change_password(self, request, pk=None):
        """
        Permite a un usuario autenticado cambiar su contraseña proporcionando
        la contraseña actual y una nueva contraseña.
        """
        from django.core.exceptions import ValidationError
        ip = obtener_ip(request) #NUEVO
        serializer = UsuarioContrasenaSerializer(data=request.data)
        if serializer.is_valid():
            try:
                logger.debug(f"Intentando cambiar contraseña para usuario con ID: {pk}") #NUEVO
                # Llama al método para actualizar la contraseña
                UsuarioDAO.actualizar_contrasena(
                    pk,
                    serializer.validated_data["current_password"],
                    serializer.validated_data["new_password"],
                    serializer.validated_data["confirm_password"],
                )
                logger_auditoria.info( #NUEVO
                    f"ip:{ip}] [accion:CAMBIAR_CONTRASENA] "
                    f"[ realizado_por :{ request .user }] [ id_afectado :{pk}]"
                )
                return Response(
                    {"mensaje": "Contraseña actualizada correctamente"},
                    status=status.HTTP_200_OK,
                )

            except UsuarioNoEncontrado_404 as e:
                logger.warning(f"Usuario no encontrado con ID {pk}: {str(e)}") #NUEVO
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

            except ValidationError as e:
                logger.warning(f"Error de validación al cambiar contraseña para usuario con ID {pk}: {str(e)}") #NUEVO
                return Response(
                    {"error": e.messages},
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)          
#################Codigo 40########################################################
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        operation_summary="Solicitar restablecimiento de contraseña",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: "Se ha enviado un enlace de restablecimiento a tu correo",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Usuario no encontrado",
        },
    )
    def request_password_reset(self, request):
        """Permite solicitar un restablecimiento de contraseña enviando un enlace o token al correo."""
        ip = obtener_ip(request) #NUEVO
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            logger.debug(f"Solicitud de restablecimiento de contraseña para email: {email}") #NUEVO
            UsuarioDAO.reset_password_request(email)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:REQUEST_PASSWORD_RESET] "
                f"[ realizado_por :{ request .user }] [ email_afectado :{email}]"
            )
            return Response(
                {"mensaje": "Se ha enviado un enlace de restablecimiento a tu correo"},
                status=status.HTTP_200_OK,
            )

        except UsuarioNoEncontrado_404 as e:
            logger.warning(f"Usuario no encontrado para email {email}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Error de validación al solicitar restablecimiento de contraseña para email {email}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 