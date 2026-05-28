from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework import status
from django.contrib.auth.models import Group
from drf_yasg.utils import swagger_auto_schema
import logging
import traceback
import time
from datetime import datetime

from core.responses import success_response, error_response
from user.serializers.roles_serializer import RoleCreateSerializer
from user.permissions import CanManageRoles



logger = logging.getLogger(__name__)

class CreateRoleView(APIView):
    """
    Crea un nuevo rol (grupo) en el sistema.

    Endpoint:
        POST /api/users/roles/create/

    Requiere:
        - Autenticación
        - Permiso para gestionar roles
    """


    permission_classes = [IsAuthenticated, CanManageRoles]
    @swagger_auto_schema(
        request_body=RoleCreateSerializer,
        tags=["Roles"],
        operation_description="Crea un nuevo grupo (rol) con nombre único"
    )
    def post(self, request):
        start_time = time.time()

        try:
            name = request.data.get("name")
            group, created = Group.objects.get_or_create(name=name)

            execution_time_ms = int((time.time() - start_time) * 1000)

            return success_response(
                status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response_message={
                    "message": f"Grupo '{name}' creado exitosamente" if created else f"El grupo '{name}' ya existe",
                    "data": {"name": group.name}
                }
            )
        except Exception as e:
            logger.error(f"Error al crear grupo: {e}")
            logger.error(traceback.format_exc())

            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                execution_time_ms=execution_time_ms,
                message="Error al crear el grupo"
            )