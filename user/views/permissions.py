# user/views/permissions.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework import status
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.responses import success_response, error_response
import logging
from drf_yasg.utils import swagger_auto_schema
from user.serializers.permissions_serializer import (
    PermissionCreateSerializer,
    AssignPermissionToGroupSerializer
)
import traceback
from user.permissions import CanManagePermissions
from datetime import datetime
import time


logger = logging.getLogger(__name__)


class CreatePermissionView(APIView):
    """
    Vista que permite crear un nuevo permiso (Permission) en el sistema.

    Endpoint:
        POST /api/permissions/create/

    Requiere:
        - Autenticación
        - Permiso personalizado `auth.can_manage_permissions`

    Esta vista permite registrar nuevos permisos indicando:
        - `codename`: identificador del permiso.
        - `name`: nombre legible.
        - `app_label`: nombre de la app asociada.
        - `model`: nombre del modelo (en minúsculas).

    Uso típico:
        {
            "codename": "can_generate_report",
            "name": "Puede generar reportes",
            "app_label": "reportes",
            "model": "informe"
        }
    """
    permission_classes = [IsAuthenticated, CanManagePermissions]
    serializer_class = PermissionCreateSerializer

    @swagger_auto_schema(
        request_body=PermissionCreateSerializer,
        tags=["Permissions"],
        operation_description="Crea un nuevo permiso con nombre, codename, app y modelo"
    )
    def post(self, request):
        start_time = time.time()

        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            codename = serializer.validated_data["codename"]
            name = serializer.validated_data["name"]
            app_label = serializer.validated_data["content_type_app_label"]
            model = serializer.validated_data["content_type_model"]

            content_type = ContentType.objects.get(app_label=app_label, model=model)
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type
            )

            mensaje = "Permiso creado exitosamente" if created else "El permiso ya existía"
            logger.info(f"Permiso '{codename}' registrado o existente")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return success_response(
                status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response={
                    "message": mensaje,
                    "data": {
                        "codename": permission.codename,
                        "name": permission.name,
                        "app_label": app_label,
                        "model": model,
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error al crear permiso: {e}")
            logger.error(traceback.format_exc())

            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                execution_time_ms=execution_time_ms,
                message="Error al crear el permiso"
            )

class AssignPermissionToGroupView(APIView):
    """
    Asigna un permiso (Permission) a un grupo (rol) existente en el sistema.

    Endpoint:
        POST /api/users/permissions/assign/

    Requiere:
        - Autenticación
        - Permiso personalizado `auth.can_manage_permissions`

    Esta vista permite vincular un permiso existente a un grupo definido. 
    El permiso debe haber sido previamente creado con un `codename`.

    Ejemplo de cuerpo de solicitud:
    {
        "group_name": "ADMIN",
        "permission_codename": "can_generate_report"
    }
    """
    permission_classes = [IsAuthenticated, CanManagePermissions]
    serializer_class = AssignPermissionToGroupSerializer

    @swagger_auto_schema(
        request_body=AssignPermissionToGroupSerializer,
        tags=["Permissions"],
        operation_description="Asigna un permiso a un grupo (rol existente) por su codename"
    )
    def post(self, request):
        start_time = time.time()

        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            group_name = serializer.validated_data["group_name"]
            group = Group.objects.get(name=group_name)
            permission_codenames = serializer.validated_data["permissions"]
            
            permisos_asignados = []
            permisos_fallidos = []

            for codename in permission_codenames:
                permiso = Permission.objects.filter(codename=codename).first()
                if permiso:
                    group.permissions.add(permiso)
                    permisos_asignados.append(codename)
                else:
                    permisos_fallidos.append(codename)
                    logger.warning(f"Permiso '{codename}' no encontrado")

            response_data = {
                "group": group.name,
                "permissions_assigned": permisos_asignados,
                "permissions_not_found": permisos_fallidos,
            }           

            execution_time_ms = int((time.time() - start_time) * 1000)

            return success_response(
                status_code=status.HTTP_200_OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response={
                    "message": f"Permisos asignados al grupo '{group_name}'",
                    "data": response_data
                }
            )

        except Exception as e:
            logger.error(f"Error al asignar permisos al grupo: {e}")
            logger.error(traceback.format_exc())

            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                execution_time_ms=execution_time_ms,
                message="Error al asignar permisos al grupo"
            )