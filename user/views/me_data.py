import logging
import time
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import Http404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from user import messages
from user.serializers import UserMeSerializer, UserUpdateMe
from user.logic import update_me_partial
from core.responses import success_response, error_response, user_not_found, empty_data


logger = logging.getLogger(__name__)

User = get_user_model()

class MeDataView(APIView):
    """
    API View que permite al usuario autenticado consultar y actualizar parcialmente sus propios datos.

    Endpoints:
        - GET /api/users/me: Devuelve los datos personales, laborales y de cuenta del usuario autenticado.
        - PATCH /api/users/me: Permite actualizar parcialmente datos personales y laborales del usuario autenticado.

    Autenticación:
        - Requiere JWT válido.
        - El token puede enviarse mediante:
            - Header: Authorization: Bearer <token>
            - Cookie: access_token

    Permisos:
        - Requiere que el usuario esté autenticado (`IsAuthenticated`).
        - Requiere permisos de modelo (`DjangoModelPermissions`).

    Buenas prácticas aplicadas:
        - Uso de `@swagger_auto_schema` para documentación OpenAPI automatizada.
        - Validaciones defensivas.
        - Delegación de la lógica de actualización a la función `update_me_partial`.
        - Registro de logs (`logger`) para trazabilidada.
        - Medición del tiempo de ejecución.
        - Respuestas centralizadas con `success_response` y `error_response`.

    Respuestas posibles:
        - 200 OK: Usuario encontrado o modificado correctamente.
        - 400 Bad Request: Datos inválidos o vacíos.
        - 401 Unauthorized: Token ausente o inválido.
        - 404 Not Found: Usuario no encontrado.
        - 500 Internal Server Error: Ha ocurrido un error inesperado. Intente nuevamente más tarde.
    """
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["Profile"],
        operation_summary="Información de Usuario",
        operation_description=(
                "Obtiene la información del usuario actualmente autenticado.\n\n"
                "Este endpoint permite al usuario consultar sus propios datos personales, laborales y de cuenta."
        ),
        responses={
            200: openapi.Response(description="Usuario encontrado."),
            401: openapi.Response(description="Sin autorización."),
            500: openapi.Response(description="Error interno del servidor."),
        }
    )

    def get(self, request):
        """
        Obtiene la información del usuario actualmente autenticado.
        Este endpoint permite al usuario consultar sus propios datos personales, laborales y de cuenta.

        Args:
            request (Request): Objeto de solicitud HTTP que contiene los datos del usuario autenticado.

        Returns:
            Response: Respuesta estructurada con código 200 y los datos del usuario si la autenticación es válida.
            Response: Código 401 si el usuario no está autenticado.
            Response: Código 500 si ocurre un error inesperado en el servidor.

        Raises:
            None (excepciones controladas internamente y devueltas como respuestas estructuradas).

        Buenas prácticas aplicadas:
            - Validación explícita de autenticación del usuario (`request.user.is_authenticated`).
            - Registro de logs con `logger` para trazabilidad de acceso.
            - Medición del tiempo de ejecución.
            - Serialización de datos.
            - Respuestas centralizadas con `success_response` y `error_response`.
        """
        start_time = time.time()

        if not request.user or not request.user.is_authenticated:
            logger.warning("Acceso no autorizado al perfil de usuario sin autenticación.")
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.AUTHENTICATION_REQUIRED
            )

        try:
            user = request.user

            logger.info("Consulta de perfil del usuario autenticado: %s", user.user_id)

            serializer = UserMeSerializer(user, context={"request": request})
            execution_time_ms = int((time.time() - start_time) * 1000)

            return success_response(
                status_code=status.HTTP_200_OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response={
                    "message": messages.USER_PROFILE_FOUND,
                    "data": serializer.data,
                }
            )

        except Exception as e:
            logger.error("Error inesperado en /users/me: %s", e, exc_info=True)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.UNKNOWN_ERROR
            )

    @swagger_auto_schema(
        tags=["Profile"],
        operation_summary="Actualización parcial de perfil",
        operation_description=(
                "Permite al usuario autenticado actualizar parcialmente sus propios datos personales y laborales.\n\n"
                "Este endpoint no permite modificar datos sensibles del sistema como correo electrónico, rol, estado "
                "de cuenta ni campos de auditoría."
                "Los campos updated_at y updated_by se asignan automáticamente."
        ),
        request_body=UserUpdateMe,
        responses={
            200: openapi.Response(description="Perfil actualizado exitosamente."),
            400: openapi.Response(description="Solicitud mal formada o datos inválidos."),
            401: openapi.Response(description="Sin autorización."),
            404: openapi.Response(description="Usuario no encontrado."),
            500: openapi.Response(description="Error interno del servidor."),
        }
    )

    def patch(self,request):
        """
        Permite al usuario autenticado actualizar parcialmente sus propios datos personales y laborales.
        Este ndpoint no permite modificar datos del sistema como email, rol, estado de cuenta, ni campos de auditoría.
        Los campos updated_at y updated_by se asignan automáticamente.

        Args:
            request (Request): Objeto de solicitud HTTP que contiene el cuerpo JSON con los datos a actualizar.

        Returns:
            Response: Código 200 si la actualización fue exitosa.
            Response: Código 400 si algún campo obligatorio está vacío o tiene formato inválido.
            Response: Código 404 si el usuario autenticado no existe en la base de datos.
            Response: Código 500 en caso de error inesperado del servidor.

        Raises:
            None (las excepciones `User.DoesNotExist` y otras son manejadas internamente).

        Buenas prácticas aplicadas:
            - Validación explícita de campos requeridos (`name`, `email`) aunque no sean modificables.
            - Medición del tiempo de ejecución.
            - Registro de logs informativos y de errores.
            - Separación de lógica de negocio en función `update_me_partial`.
            - Respuestas uniformes mediante `success_response`, `error_response`, `empty_data`, y `user_not_found`.
            - Validación estructurada de entrada mediante el serializer `UserUpdateMe`.
        """
        logger.info(f"Solicitud de actualización parcial de usuario por {request.user.email}")
        start_time = time.time()
        user_id=request.user.user_id

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

            exito, cuerpo, codigo = update_me_partial(user, data)
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