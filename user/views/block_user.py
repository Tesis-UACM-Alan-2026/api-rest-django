"""
Vista API para bloquear (desactivar) un usuario del sistema.

Incluye:
- Validación de permisos específicos para bloqueo
- Verificación del estado actual del usuario
- Registro de auditoría
- Estandarización de la respuesta con éxito o error

Endpoint:
    POST /api/users/{user_id}/block/
"""

import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
# Importación de funciones de respuesta estandarizada
from core.responses import success_response, error_response
import time
# Lógica de negocio separada para reutilización y pruebas
from user.logic import bloquear_usuario
from user import messages
from user.serializers import UserSerializer
from drf_yasg import openapi



logger = logging.getLogger(__name__)

User = get_user_model()
class BlockUserView(APIView):
    """
    Bloquea (desactiva) un usuario, si se tiene el permiso adecuado.

    Permite:
    - Validar el permiso específico 'can_block_user' y 'can_manage_users'
    - Ejecutar la lógica de bloqueo desde el archivo logic.py
    - Devolver una respuesta JSON estandarizada
    """
    permission_classes = [IsAuthenticated]
    serializer_class =UserSerializer
    queryset = User.objects.all() 


    @swagger_auto_schema(
        request_body=None,
        tags=["Users"],
        operation_summary="Bloquea un usuario",
        operation_description="Bloquea a un usuario específico, impidiendo su acceso al sistema. Esta acción marca el campo is_active = false y registra trazabilidad en los campos blocked_at y blocked_by. Solo usuarios con permisos administrativos pueden ejecutar esta acción.",
        manual_parameters=[
            openapi.Parameter(
                    name = "user_id",
                    in_ = openapi.IN_PATH,
                    type = openapi.TYPE_STRING,
                    format = openapi.FORMAT_UUID,
                    required = True,
                    description = "UUID del usuario"
            )
        ],
        responses={
            200:"Solicitud exitosa",
            201:"Usuario bloqueado exitosamente",
            400:"Solicitud mal formada",
            401:"No autenticado",
            403:"Sin permisos",
            404:"No encontrado",
            500:"Error interno"
        }
    )
    def post(self, request, user_id=None):
        """  
        Bloquea un usuario por su user_id(uuid)
        Args:
            request(HTTPRequest): Objeto de solicitud HTTP
            user_id(UUID): ID único del usuario a bloquear
        Returns:
            Response:
                200: Si éxito
                404: Si no existe
                400: Si la solicitud esta mal formada
                403: Si no tiene permisos
                500: Si hay un error interno
        Buenas prácticas
            - Logger, control de permisos, tiempo de ejecución
        
        """
        # Verificamos si el usuario autenticado tiene permiso para bloquear usuarios
        start_time=time.time()

        
        if not (request.user.has_perm("user.can_block_user") or request.user.has_perm("user.can_manage_users")):
            logger.warning(f"Usuario sin permiso intentó bloquear a otro: {request.user.email}")
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message=messages.BLOCK_NO_PERMISSION
            )

        # Se delega la lógica de negocio al archivo logic.py
        exito, cuerpo, codigo = bloquear_usuario(user_id, request.user)

        end_time = time.time()
        execution_time_ms = int((end_time - start_time) * 1000)

        # Si hay exito se manda un success response
        # Si no se manda un error
        if exito:
            logger.info(f"Usuario {user_id} bloqueado por {request.user.email}")
            return success_response(
                status_code=status.HTTP_200_OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response={
                    "message": cuerpo.get("detail", "Usuario bloqueado correctamente."),
                    "data": cuerpo
                }
            )
        else:
            return error_response(
                status_code=codigo,
                message=cuerpo
            )