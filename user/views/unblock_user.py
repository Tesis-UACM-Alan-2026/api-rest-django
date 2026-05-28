"""
    Permite desbloquear un usuario que previamente fue bloqueado por el sistema.
    Este endpoint requiere permisos especiales para poder ejecutarse.

    Endpoint:

        POST /api/users/unblock

    Parametros:
        - user_id: UUID del usuario a bloquear

    Retorna:
        - 200 OK si fue exitoso
        - 403 Forbidden si no se tienen permisos
        - 400 Bad Request si el usuario ya está desbloqueado
        - 404 Not Found si el usuario no existe
    """
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,DjangoModelPermissions
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
# Importación de funciones de respuesta estandarizada
from core.responses import success_response, error_response
import time
from datetime import datetime
# Lógica de negocio separada para reutilización y pruebas
from user.logic import desbloquear_usuario
from user import messages
from user.models import User
from drf_yasg import openapi
logger = logging.getLogger(__name__)

User = get_user_model()

class UnBlockUserView(APIView):
    
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        request_body=None,
        tags=["Users"],
        operation_summary="Desbloquear un usuario",
        operation_description="Desbloquea a un usuario previamente bloqueado (is_active = false), restaurando su capacidad para acceder al sistema. La acción actualiza el campo is_active = true y registra trazabilidad mediante los campos unblocked_at y unblocked_by. Solo usuarios con permisos administrativos pueden ejecutarla.",
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
            201:"Usuario desbloqueado exitosamente",
            400:"Solicitud mal formada",
            401:"No autenticado",
            403:"Sin permisos",
            404:"No encontrado",
            500:"Error interno"
        }
    )
    def post (self,request,user_id=None):
        """  
        Desbloquea un usuario por su user_id(uuid)
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
        start_time=time.time()
        if not (request.user.has_perm("user.can_block_user") or request.user.has_perm("user.can_manage_users")) :
            logger.warning(f"Usuario sin permiso intento desbloquear a otro {request.user.email}")
            return error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message=messages.UNBLOCK_NO_PERMISSION
                )
        end_time = time.time()
        execution_time_ms = int((end_time - start_time) * 1000)
        #Se llama a la logica
        exito,cuerpo,codigo=desbloquear_usuario(user_id,request.user)

        if exito:
            logger.info(f"Usuario {user_id} desbloqueado por {request.user.email}")
            return success_response(
                    status_code=status.HTTP_200_OK,
                    execution_time_ms=execution_time_ms,
                    request=request,
                    response=cuerpo
                )
        else:
            return error_response(
                status_code=codigo,
                message=cuerpo
            )