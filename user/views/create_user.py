"""
Vista API para la creación de nuevos usuarios.

Incluye:
- Permisos requeridos
- Uso de lógica separada en logic.py
- Documentación Swagger/OpenAPI
- Respuestas estandarizadas
"""

from datetime import datetime
import time
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from user.serializers import UserSerializer

from user.logic import crear_usuario
from core.responses import success_response, error_response
from user import messages
logger = logging.getLogger(__name__)

User = get_user_model()

class UserCreateView(APIView):
    """
    Crea un nuevo usuario en el sistema mediante una solicitud POST.

    Endpoint:
        POST /api/users/create/

    Requiere:
        - Autenticación
        - Permiso personalizado `auth.can_manage_roles` (asignado a quienes gestionan usuarios)
    """
    permission_classes = [IsAuthenticated,]
    queryset = User.objects.all()
    serializer_class = UserSerializer


    @swagger_auto_schema(
        request_body=UserSerializer,
        tags=["Users"],
        operation_summary="Crea un nuevo usuario ",
        operation_description="Crea un nuevo usuario en el sistema. Este endpoint es exclusivo para administradores autorizados y permite registrar tanto los datos personales como laborales del usuario. Algunos campos del sistema y de auditoría se asignan automáticamente.",
        responses={
            200:"Solicitud exitosa",
            201:"Usuario creado de manera exitosa",
            400:"Solicitud mal formada",
            401:"No autenticado",
            403:"Sin permisos",
            404:"No encontrado",
            500:"Error interno"
        }
    )
    
    def post(self, request):
        """
        Crea un nuevo usuario
        Args: 
            request (HTTPRequest): Objeto de solicitud HTTP
        Returns:
            200: Respuesta exitosa
            201: Creación de usuario exitosa
            401: sin autorizacion
            400: solicitud mal formada
            403: No tiene los permisos requeridos
            404: No se encontro el recurso
            500: Error interno 
        Raises:
            Exception: Si ocurre que el usuario ya existe
            Devuelve Http400: si los datos no son correctos o la validacion de campos como (curp,rfc,contraseña,etc) no son validos
        """
        start_time = time.time()
        logger.info(f"Solicitud de creación de usuario por {request.user.email}")

        # Validamos que tenga el permiso de crear usuarios
        if not (request.user.has_perm("user.can_manage_users") or request.user.has_perm("user.can_create_users")):
            logger.warning(f"Usuario sin permiso para crear usuarios: {request.user.email}")
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message=messages.CREATE_NO_PERMISSION
            )
        
        try:
            exito, cuerpo, codigo = crear_usuario(request.data)
            execution_time_ms = int((time.time() - start_time) * 1000)

            if exito:
                # Ajuste: el cuerpo ya contiene 'detail' y 'user' serializado
                data=cuerpo.get("data")
                response_message = {
                    "message": cuerpo.get("message"),
                    "data": {
                        'id':data['user_id'],
                    }
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
                    message=cuerpo.get('detail'),
                )

        except Exception as e:
            logger.error(f"Error inesperado al crear usuario: {e}", exc_info=True)
            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=execution_time_ms,
                message=messages.CREATE_ERROR
            )
