"""
Vista API para restaurar (restauracion logica) un usuario del sistema.

Incluye:
- Validación de permisos específicos para bloqueo
- Verificación del estado actual del usuario
- Registro de fecha de la restauracion
- Registro del responsable de la restauración
- Estandarización de la respuesta con éxito o error

Endpoint:
    POST /users/{user_id}/restore
"""
import logging
import time
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated,DjangoModelPermissions
from drf_yasg.utils import swagger_auto_schema
from core.responses import success_response, error_response
from rest_framework import status
from user import messages
from user.logic import restore_user
from django.http import Http404
logger = logging.getLogger(__name__)

User = get_user_model()
class RestoreUserView(APIView):
    """
    Restaura (restaura logicamente) un usuario, si se tiene el permiso adecuado.

    Permite:
    - Validar el permiso específico 'can_manage_users' o 'can_restore_user'
    - Ejecutar la lógica de bloqueo desde el archivo logic.py
    - Devolver una respuesta JSON estandarizada
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    @swagger_auto_schema(
        request_body=None,
        tags=["Users"],
        operation_description="Restaura un usuario previamente eliminado lógicamente (soft delete). Esto implica cambiar restaurar, registrar la fecha y el responsable de la restauración. Solo accesible para usuarios con permisos administrativos."
    )

    def post(self,request, user_id=None):
        try:
            # Verificamos si el usuario autenticado tiene permiso para restaurar usuarios.
            start_time = time.time()

            if not (request.user.has_perm("user.can_manage_users") or
                    request.user.has_perm("user.can_restore_user")):
                logger.warning(f"Usuario sin permisos intentó restaurar a otro: {request.user.email}")
                return error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message=messages.INSUFFICIENT_PERMISSIONS
                )
            
            #Se llama a la logica
            exito, cuerpo, codigo = restore_user(user_id, request.user)
            
            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)        

            #Si la restauración falla, se registra el error y se devuelve una respuesta de error
            if not exito:
                logger.error(f"Error al restaurar usuario {user_id} por {request.user.email}: {cuerpo}")
                return error_response(
                    status_code=codigo,
                    execution_time_ms= execution_time_ms,
                    message=cuerpo
                ) 

            #Si todo sale bien, se registra la restauración
            logger.info(f"Usuario {user_id} restaurado por {request.user.email}")
            return success_response(
                status_code=status.HTTP_200_OK,
                execution_time_ms= execution_time_ms,
                request=request,
                response=cuerpo,
            )
        #captura el caso de que el usuario no exista desde la clase logic.py de nuestro def 'restore_user'
        except Http404:
            logger.error(f"Usuario {user_id} no encontrado para restauración.")
            return error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=messages.USER_NOT_FOUND.format(uuid=user_id),
            )
        #Captura cualquier otro error inesperado y lo registra en el log.
        except Exception as e:
            logger.error(f"Error inesperado al restaurar usuario {user_id} error: {str(e)}")
            return error_response(
                    status_code=codigo,
                    execution_time_ms= execution_time_ms,
                    message=messages.UNKNOWN_ERROR
                ) 