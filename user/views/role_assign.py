"""
Vista API para asignación de roles a usuarios del sistema.

Esta vista permite modificar el rol principal de un usuario existente, proporcionando
un mecanismo centralizado para la gestión de permisos y responsabilidades dentro
del sistema de gestión hospitalaria.

Características:
    - Asignación de rol único: Actualiza el campo 'role' del usuario
    - Validación de roles: Verifica que el rol sea válido según RoleChoices
    - Trazabilidad: Registra quién y cuándo realizó el cambio de rol
    - Formato de entrada: Array con un objeto conteniendo el roleId

Autenticación y permisos:
    - Requiere autenticación JWT válida
    - Requiere permiso 'user.change_user'
    - Verificación manual de credenciales para respuestas 401/403 consistentes

Endpoint:
    POST /api/users/{user_id}/assign-role/

Parámetros:
    - user_id (UUID): Identificador único del usuario

Cuerpo de la solicitud:
    ```json
    [{"roleId": "Solicitante"}]
    ```

Roles válidos:
    - Según definición en user.choices.RoleChoices
    - Ejemplos: "Solicitante", "Administrador", etc.

Códigos de respuesta:
    - 200: Rol asignado exitosamente
    - 400: Datos inválidos o rol no válido
    - 401: Sin autorización (credenciales inválidas)
    - 403: Solicitud prohibida (permisos insuficientes)
    - 404: Usuario no encontrado
    - 500: Error interno del servidor

Notas:
    - El formato de entrada usa camelCase (roleId) que se convierte automáticamente
    - Solo se permite un rol por usuario (reemplaza el rol anterior)
    - La operación actualiza el campo 'updated_by' y 'updated_at'
    - Se registra la trazabilidad completa del cambio
"""

import logging
import time
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from django.http import Http404
from user.logic import assign_user_role
from user.serializers.asignar_role_serializer import AssignRoleSerializer
from core.responses import success_response, error_response
from rest_framework_simplejwt.authentication import JWTAuthentication
from user import messages

logger = logging.getLogger(__name__)
User = get_user_model()

class AssignRoleToUserView(APIView):
    """
    Vista para asignar un nuevo rol a un usuario existente.

    Recibe un array con un único objeto conteniendo el rol a asignar.
    El valor de `roleId` debe ser uno válido definido en los choices del sistema.

    Endpoint:
        POST /users/{user_id}/assign-role

    Requiere autenticación y permisos adecuados.
    """

    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]
    queryset = User.objects.all()

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Asigna un nuevo rol a un usuario específico, identificado por su user_id. Esta operación requiere permisos especiales y es registrada en el historial del usuario para fines de auditoría.",
        request_body=AssignRoleSerializer(many=True),
        responses={
            200: "Rol asignado exitosamente.",
            400: "Solicitud mal formada",
            401: "Sin autorización.",
            403: "Solicitud prohibida.",
            404: "No encontrado.",
            500: "Error interno del servidor."
        }
    )
    def post(self, request, user_id):
        """
        Procesa la asignación de un nuevo rol a un usuario específico.

        Args:
            request (Request): Objeto de solicitud HTTP con datos del rol a asignar.
            user_id (UUID): Identificador único del usuario al que se asignará el rol.

        Returns:
            Response: Respuesta JSON con el resultado de la operación de asignación.
        """
        start_time = time.time()
        
        if not request.user or not request.user.is_authenticated:
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.AUTHENTICATION_REQUIRED
            )
        
        logger.info(f"Solicitud de asignación de rol a usuario {user_id} por {request.user.email}")
        
        try:
            if not request.user.has_perm("user.change_user"):
                return error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    message=messages.INSUFFICIENT_PERMISSIONS,
                )
            
            serializer = AssignRoleSerializer(data=request.data, many=True)
            
            if not serializer.is_valid():
                logger.error(f"Error de validación del serializer: {serializer.errors}")
                execution_time_ms = int((time.time() - start_time) * 1000)
                return error_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    execution_time_ms=execution_time_ms,
                    message=messages.ROLE_INVALID
                )
            
            role_id = serializer.validated_data[0]['role']
            
            exito, cuerpo, codigo = assign_user_role(user_id, role_id, request.user)
            execution_time_ms = int((time.time() - start_time) * 1000)

            if exito:
                return success_response(
                    status_code=codigo,
                    execution_time_ms=execution_time_ms,
                    request=request,
                    response=cuerpo["detail"]
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
                message=messages.USER_NOT_FOUND.format(uuid=user_id)
            )
        except Exception as e:
            logger.error(f"Error inesperado al asignar rol: {e}", exc_info=True)
            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=execution_time_ms,
                message=messages.UNKNOWN_ERROR  # O el mensaje específico actual
            )