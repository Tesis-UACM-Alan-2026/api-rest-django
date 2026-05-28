import logging
import time

from http import HTTPStatus
from django.http import Http404
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from user import messages
from user.serializers import UserSerializer, UserUpdate
from user.logic import get_user_by_id, actualiza_usuario_parcial,delete_user
from user.permissions import PERMISSION_CODENAMES

from core.responses import success_response, error_response, user_not_found, empty_data

logger = logging.getLogger(__name__)

User = get_user_model()

class UserDataView(APIView):
    """
    API View que permite consultar y actualizar parcialmente los datos de un usuario identificado por su UUID.

    Endpoints:
        - GET /api/users/<user_id>/: Consulta un usuario específico.
        - PATCH /api/users/<user_id>/: Actualiza parcialmente los datos de un usuario.

    Autenticación:
        - Requiere JWT válido, ya sea por header o cookie.

    Permisos:
        - Requiere que el usuario esté autenticado (`IsAuthenticated`) y tenga permisos de modelo (`DjangoModelPermissions`).

    Buenas prácticas aplicadas:
        - Decoradores `@swagger_auto_schema` para documentación automática OpenAPI.
        - Uso de `logging` para trazabilidad.
        - Medición del tiempo de ejecución por petición.
        - Validación defensiva de datos de entrada.
        - Separación de lógica en funciones auxiliares (`get_user_by_id`, `actualiza_usuario_parcial`).
        - Respuestas centralizadas con `success_response` y `error_response`.
    """
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["Users"],
        operation_summary="Información de Usuario",
        operation_description="Recupera la información completa de un usuario específico, identificado por su user_id. Este endpoint está restringido a usuarios con permisos administrativos.",

        manual_parameters=[
            openapi.Parameter(
                name="user_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True,
                description="`user_id` del usuario en formato UUID."
            )
        ],
        responses={
            200: openapi.Response(description="Usuario encontrado."),
            401: openapi.Response(description="Sin autorización."),
            403: openapi.Response(description="Solicitud prohibida."),
            404: openapi.Response(description="No encontrado."),
            500: openapi.Response(description="Error interno del servidor."),
        }
    )

    def get(self, request, user_id):
        """
        Maneja la solicitud GET para consultar los datos de un usuario.

        Args:
            request (HttpRequest): Objeto de la solicitud HTTP.
            user_id (UUID): Identificador único del usuario a consultar.

        Returns:
            Response: Objeto de respuesta HTTP con:
                - status 200 y datos del usuario si se encuentra.
                - status 404 si no existe.
                - status 500 si ocurre un error inesperado.

        Raises:
            Http404: Si el usuario no se encuentra.
            Exception: Cualquier error inesperado capturado y registrado.

        Buenas prácticas:
            - Uso de logger para auditoría.
            - Manejo explícito de errores.
            - Respuesta estructurada conforme a contrato de la API.
        """
        start_time = time.time()

        if not request.user or not request.user.is_authenticated:
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.AUTHENTICATION_REQUIRED
            )

        try:
            user = request.user
            if not (
                user.has_perm(f"user.{PERMISSION_CODENAMES['CAN_MANAGE_USERS']}") or
                user.has_perm(f"user.{PERMISSION_CODENAMES['CAN_VIEW_USERS']}")
            ):
                logger.warning("Acceso denegado para el usuario %s", user_id)
                return error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    execution_time_ms=(int(time.time() - start_time) * 1000),
                    message=messages.INSUFFICIENT_PERMISSIONS,
                )

            logger.info("Consulta de usuario por su id: %s", user_id)

            # Lógica -> obtener y serializar el usuario
            user = get_user_by_id(user_id)
            serializer = UserSerializer(user, context={'request': request})

            execution_time_ms = int((time.time() - start_time) * 1000)

            return success_response(
                status_code=status.HTTP_200_OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response={
                    "message": messages.USER_FOUND,
                    "data": serializer.data
                }
            )

        except Http404:
            logger.warning("Usuario no encontrado: %s", user_id)
            return error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.USER_NOT_FOUND.format(uuid=user_id)
            )

        except Exception as e:
            logger.error("Error inesperado al consultar usuario %s: %s", user_id, e, exc_info=True)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.UNKNOWN_ERROR
            )

    ## Aquí empieza el código para hacer el PATCH.

    @swagger_auto_schema(
        request_body=UserUpdate,
        tags=["Users"],
        operation_description="Actualiza parcialmente los datos de un usuario específico por su UUID. Este endpoint está restringido a administradores y permite modificar información personal, laboral y de control, excluyendo campos del sistema que son asignados automáticamente. Los campos updated_at y updated_by se asignan automáticamente."
    )
    def patch(self,request, user_id, *args, **kwargs):

        """
        Maneja la solicitud PATCH para actualizar parcialmente un usuario.

        Args:
            request (HttpRequest): Objeto de la solicitud HTTP con datos JSON.
            user_id (UUID): Identificador único del usuario a modificar.
            *args: Argumentos adicionales.
            **kwargs: Argumentos adicionales por clave.

        Returns:
            Response: Objeto de respuesta HTTP con:
                - status 200 si se actualizó correctamente.
                - status 400 si hay datos inválidos.
                - status 404 si el usuario no existe.
                - status 500 si ocurre un error inesperado.

        Raises:
            User.DoesNotExist: Si no se encuentra el usuario.
            Exception: Si ocurre un error inesperado (registrado con logger).

        Buenas prácticas:
            - Validación defensiva de campos como `email` y `name`.
            - Desacoplamiento de lógica en `actualiza_usuario_parcial`.
            - Medición de tiempo de ejecución para auditoría.
            - Registro detallado de errores y excepciones.
        """
        logger.info(f"Solicitud de actualización parcial de usuario por {request.user.email}")
        start_time = time.time()

        try:
            user = User.objects.get(user_id=user_id)

            data = request.data
            email = data.get('email')
            name = data.get('name')

            if email is not None and not email.strip():
                return empty_data(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    execution_time_ms=int((time.time() - start_time)*1000),
                    message=messages.INVALID_DATA
                )

            if name is not None and not name.strip():
                return empty_data(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    execution_time_ms=int((time.time() - start_time)*1000),
                    message=messages.INVALID_DATA
                )

            exito, cuerpo, codigo = actualiza_usuario_parcial(user, data)
            execution_time_ms=int((time.time() - start_time)*1000)

            if exito:
                return success_response(
                    status_code=HTTPStatus.OK,
                    execution_time_ms=execution_time_ms,
                    request=request,
                    response=messages.UPDATE_PARTIAL_SUCCESS
                )
            else:
                logger.error(f"Error al actualizar usuario {user_id}: {cuerpo}")
                return error_response(
                    status_code=codigo if codigo else HTTPStatus.INTERNAL_SERVER_ERROR,
                    execution_time_ms=execution_time_ms,
                    message=cuerpo if cuerpo else messages.UNKNOWN_ERROR
                )

        except User.DoesNotExist:
            return user_not_found(
                status_code=status.HTTP_404_NOT_FOUND,
                execution_time_ms=int((time.time() - start_time)*1000),
                message=messages.USER_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar usuario {user_id}")
            return error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                execution_time_ms=int((time.time() - start_time)*1000),
                message=str(e)
            )

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Elimina lógicamente a un usuario específico. Esto no borra el registro de la base de datos, sino que marca el usuario como eliminado (is_deleted = true) y registra la fecha y el responsable de la eliminación (deleted_at, deleted_by). El usuario eliminado no podrá autenticarse.",
        responses={
            200: "Usuario eliminado correctamente",
            401: "Sin autorización",
            403: "Solicitud prohibida",
            404: "Usuario no encontrado",
            500: "Error interno del servidor"
        }
    )    
    def delete(self, request, user_id):
        """
        Realiza la eliminación lógica de un usuario del sistema.

        Args:
            request (Request): Objeto de solicitud HTTP con datos de autenticación.
            user_id (UUID): Identificador único del usuario a eliminar lógicamente.

        Returns:
            Response: Respuesta JSON con el resultado de la operación de eliminación.
        """
        start_time = time.time()
        
        if not request.user or not request.user.is_authenticated:
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.AUTHENTICATION_REQUIRED
            )
        
        logger.info(f"Solicitud de eliminacion lógica de usuario {user_id} por {request.user.email}")
        
        try:
            if not request.user.has_perm("user.delete_user"):
                return error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    message=messages.INSUFFICIENT_PERMISSIONS,
                )
            
            exito, cuerpo, codigo = delete_user(user_id, request.user)
            execution_time_ms = int((time.time() - start_time) * 1000)

            if exito:
                response_message = {
                    "message": "Usuario eliminado exitosamente"
                }
                return success_response(
                    status_code=codigo, 
                    execution_time_ms=execution_time_ms,
                    request=request, 
                    response=response_message
                )
            else:
                return error_response(
                    status_code=codigo, 
                    execution_time_ms=execution_time_ms,
                    message=cuerpo["detail"]
                )
        
        except Http404:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                execution_time_ms=execution_time_ms,
                message=messages.USER_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"Error inesperado al eliminar usuario: {e}", exc_info=True)
            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=execution_time_ms,
                message=messages.UNKNOWN_ERROR
            )