import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from core.utils import obtener_ip, auditar
from gestion_permisos.permissions import HasPermission
from gestion_permisos.service import PermisoService, RolService
from gestion_permisos.VO.permisoVO import PermisoVO
from gestion_permisos.VO.rolVO import RolVO
from gestion_permisos.serializers import (
    PermisoSerializer,
    RolSerializer,
    RolPermisosSerializer,
)
from gestion_permisos.exceptions.permisoExceptions import (
    PermisosError,
    DatosInvalidosPermisos_400,
    PermisoNoEncontrado_404,
    PermisoDuplicado_409,
    PermisoEnUso_409,
    RolNoEncontrado_404,
    RolDuplicado_409,
    RolEnUso_409,
)

permisoService = PermisoService()
rolService = RolService()

logger = logging.getLogger('gestion_permisos')  # logs técnicos

# Código HTTP que corresponde a cada excepción del módulo
CODIGOS_HTTP = {
    DatosInvalidosPermisos_400: status.HTTP_400_BAD_REQUEST,
    PermisoNoEncontrado_404: status.HTTP_404_NOT_FOUND,
    RolNoEncontrado_404: status.HTTP_404_NOT_FOUND,
    PermisoDuplicado_409: status.HTTP_409_CONFLICT,
    RolDuplicado_409: status.HTTP_409_CONFLICT,
    PermisoEnUso_409: status.HTTP_409_CONFLICT,
    RolEnUso_409: status.HTTP_409_CONFLICT,
}


def responder_error(error):
    """Convierte una excepción del módulo en la respuesta HTTP correspondiente."""
    codigo = CODIGOS_HTTP.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)

    if codigo >= 500:
        logger.error(f"Error interno en gestión de permisos: {str(error)}")
    else:
        logger.warning(f"{type(error).__name__}: {str(error)}")

    return Response({"error": str(error)}, status=codigo)


# =====================================================================
#                              PERMISOS
# =====================================================================
class PermisosViewSet(viewsets.ViewSet):
    """API para la gestión de Permisos."""

    permission_classes = [IsAuthenticated, HasPermission]
    permisos_requeridos = {
        "list": "permisos.ver",
        "retrieve": "permisos.ver",
        "create": "permisos.crear",
        "update": "permisos.editar",
        "partial_update": "permisos.editar",
        "destroy": "permisos.eliminar",
    }

    @swagger_auto_schema(
        operation_summary="Listar permisos",
        responses={200: PermisoSerializer(many=True)},
    )
    def list(self, request):
        permisos_vo = permisoService.listar_permisos()
        serializer = PermisoSerializer(permisos_vo, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Consultar permiso",
        responses={
            200: PermisoSerializer(),
            404: "Permiso no encontrado.",
        },
    )
    def retrieve(self, request, pk=None):
        try:
            permiso_vo = permisoService.obtener_permiso(pk)
            return Response(
                PermisoSerializer(permiso_vo).data,
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Crear permiso",
        request_body=PermisoSerializer,
        responses={
            201: PermisoSerializer(),
            400: "Datos inválidos.",
            409: "Ya existe un permiso con ese codename.",
        },
    )
    def create(self, request):
        ip = obtener_ip(request)

        serializer = PermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            permiso_vo = PermisoVO.desde_dict(serializer.validated_data)
            creado_vo = permisoService.crear_permiso(permiso_vo)
            auditar(ip, "CREAR_PERMISO", request, permiso_id=creado_vo.id)

            return Response(
                PermisoSerializer(creado_vo).data,
                status=status.HTTP_201_CREATED
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Actualizar permiso",
        request_body=PermisoSerializer,
        responses={
            200: PermisoSerializer(),
            400: "Datos inválidos.",
            404: "Permiso no encontrado.",
            409: "Ya existe un permiso con ese codename.",
        },
    )
    def update(self, request, pk=None):
        ip = obtener_ip(request)

        serializer = PermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            permiso_vo = PermisoVO.desde_dict(serializer.validated_data)
            actualizado_vo = permisoService.actualizar_permiso(pk, permiso_vo)
            auditar(ip, "ACTUALIZAR_PERMISO", request, permiso_id=pk)

            return Response(
                PermisoSerializer(actualizado_vo).data,
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Actualizar parcialmente un permiso",
        request_body=PermisoSerializer,
        responses={
            200: PermisoSerializer(),
            400: "Datos inválidos.",
            404: "Permiso no encontrado.",
            409: "Ya existe un permiso con ese codename.",
        },
    )
    def partial_update(self, request, pk=None):
        ip = obtener_ip(request)

        serializer = PermisoSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            permiso_vo = PermisoVO.desde_dict(serializer.validated_data)
            actualizado_vo = permisoService.actualizar_permiso_parcial(pk, permiso_vo)
            auditar(ip, "ACTUALIZAR_PERMISO_PARCIAL", request, permiso_id=pk)

            return Response(
                PermisoSerializer(actualizado_vo).data,
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Eliminar permiso",
        operation_description=(
                "Elimina un permiso. No se permite si está asignado a algún rol."
        ),
        responses={
            200: "Permiso eliminado correctamente.",
            404: "Permiso no encontrado.",
            409: "El permiso está asignado a uno o más roles.",
        },
    )
    def destroy(self, request, pk=None):
        ip = obtener_ip(request)
        try:
            permisoService.eliminar_permiso(pk)
            auditar(ip, "ELIMINAR_PERMISO", request, permiso_id=pk)

            return Response(
                {"mensaje": "Permiso eliminado correctamente."},
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)


# =====================================================================
#                                ROLES
# =====================================================================
class RolesViewSet(viewsets.ViewSet):
    """API para la gestión de Roles y de sus permisos."""

    permission_classes = [IsAuthenticated, HasPermission]
    permisos_requeridos = {
        "list": "roles.ver",
        "retrieve": "roles.ver",
        "create": "roles.crear",
        "update": "roles.editar",
        "partial_update": "roles.editar",
        "destroy": "roles.eliminar",
        "asignar_permisos": "roles.asignar_permisos",
        "quitar_permisos": "roles.asignar_permisos",
    }

    @swagger_auto_schema(
        operation_summary="Listar roles",
        responses={200: RolSerializer(many=True)},
    )
    def list(self, request):
        roles_vo = rolService.listar_roles()
        serializer = RolSerializer(roles_vo, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Consultar rol",
        responses={
            200: RolSerializer(),
            404: "Rol no encontrado.",
        },
    )
    def retrieve(self, request, pk=None):
        try:
            rol_vo = rolService.obtener_rol(pk)
            return Response(
                RolSerializer(rol_vo).data,
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Crear rol",
        request_body=RolSerializer,
        responses={
            201: RolSerializer(),
            400: "Datos inválidos.",
            409: "Ya existe un rol con ese nombre.",
        },
    )
    def create(self, request):
        ip = obtener_ip(request)

        serializer = RolSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol_vo = RolVO.desde_dict(serializer.validated_data)
            creado_vo = rolService.crear_rol(rol_vo)
            auditar(ip, "CREAR_ROL", request, rol_id=creado_vo.id)

            return Response(
                RolSerializer(creado_vo).data,
                status=status.HTTP_201_CREATED
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Actualizar rol",
        request_body=RolSerializer,
        responses={
            200: RolSerializer(),
            400: "Datos inválidos.",
            404: "Rol no encontrado.",
            409: "Ya existe un rol con ese nombre.",
        },
    )
    def update(self, request, pk=None):
        ip = obtener_ip(request)

        serializer = RolSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol_vo = RolVO.desde_dict(serializer.validated_data)
            actualizado_vo = rolService.actualizar_rol(pk, rol_vo)
            auditar(ip, "ACTUALIZAR_ROL", request, rol_id=pk)

            return Response(
                RolSerializer(actualizado_vo).data,
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Actualizar parcialmente un rol",
        request_body=RolSerializer,
        responses={
            200: RolSerializer(),
            400: "Datos inválidos.",
            404: "Rol no encontrado.",
            409: "Ya existe un rol con ese nombre.",
        },
    )
    def partial_update(self, request, pk=None):
        ip = obtener_ip(request)

        serializer = RolSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol_vo = RolVO.desde_dict(serializer.validated_data)
            actualizado_vo = rolService.actualizar_rol_parcial(pk, rol_vo)
            auditar(ip, "ACTUALIZAR_ROL_PARCIAL", request, rol_id=pk)

            return Response(
                RolSerializer(actualizado_vo).data,
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Eliminar rol",
        operation_description=(
                "Elimina un rol. No se permite si está asignado a algún usuario."
        ),
        responses={
            200: "Rol eliminado correctamente.",
            404: "Rol no encontrado.",
            409: "El rol está asignado a uno o más usuarios.",
        },
    )
    def destroy(self, request, pk=None):
        ip = obtener_ip(request)
        try:
            rolService.eliminar_rol(pk)
            auditar(ip, "ELIMINAR_ROL", request, rol_id=pk)

            return Response(
                {"mensaje": "Rol eliminado correctamente."},
                status=status.HTTP_200_OK
            )

        except PermisosError as error:
            return responder_error(error)

    # ------------------- Permisos de un rol -------------------
    @swagger_auto_schema(
        operation_summary="Asignar permisos a un rol",
        operation_description="Agrega los permisos indicados. Los ya asignados se ignoran.",
        request_body=RolPermisosSerializer,
        responses={
            200: RolSerializer(),
            400: "Datos inválidos o permisos inexistentes.",
            404: "Rol no encontrado.",
        },
    )
    @action(detail=True, methods=["post"], url_path="asignar-permisos")
    def asignar_permisos(self, request, pk=None):
        ip = obtener_ip(request)

        serializer = RolPermisosSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            permisos_ids = serializer.validated_data["permisos"]
            rol_vo = rolService.asignar_permisos(pk, permisos_ids)
            auditar(
                ip, "ASIGNAR_PERMISOS_ROL", request,
                rol_id=pk, permisos=sorted(set(permisos_ids))
            )

            return Response(RolSerializer(rol_vo).data, status=status.HTTP_200_OK)

        except PermisosError as error:
            return responder_error(error)

    @swagger_auto_schema(
        operation_summary="Quitar permisos de un rol",
        operation_description="Quita los permisos indicados. Los no asignados se ignoran.",
        request_body=RolPermisosSerializer,
        responses={
            200: RolSerializer(),
            400: "Datos inválidos.",
            404: "Rol no encontrado.",
        },
    )
    @action(detail=True, methods=["post"], url_path="quitar-permisos")
    def quitar_permisos(self, request, pk=None):
        ip = obtener_ip(request)

        serializer = RolPermisosSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            permisos_ids = serializer.validated_data["permisos"]
            rol_vo = rolService.quitar_permisos(pk, permisos_ids)
            auditar(
                ip, "QUITAR_PERMISOS_ROL", request,
                rol_id=pk, permisos=sorted(set(permisos_ids))
            )

            return Response(RolSerializer(rol_vo).data, status=status.HTTP_200_OK)

        except PermisosError as error:
            return responder_error(error)