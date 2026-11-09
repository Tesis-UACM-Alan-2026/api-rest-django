import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from core.utils import obtener_ip, auditar
from gestion_permisos.permissions import HasPermission
from autentificacion.service import LogService
from autentificacion.serializers import (
    LogAuditoriaQuerySerializer,
    LogTecnicoQuerySerializer,
    LogConsultaSerializer,
)
from autentificacion.exceptions.autenticacionExceptions import LogNoDisponible_500

logService = LogService()
logger = logging.getLogger(__name__)


class LogAuditoriaView(APIView):
    """
    GET /api/auth/logs/auditoria/
    Devuelve entradas del log de auditoría (más recientes primero).
    Requiere el permiso 'logs.ver_auditoria'.

    Parámetros opcionales de query:
      ?usuario=admin@correo.com
      ?accion=LOGIN_EXITOSO
      ?limite=50          (1 a 1000, por defecto 100)
    """

    permission_classes = [IsAuthenticated, HasPermission]
    permiso_requerido = "logs.ver_auditoria"

    @swagger_auto_schema(
        operation_summary="Consultar el log de auditoría",
        query_serializer=LogAuditoriaQuerySerializer,
        responses={
            200: LogConsultaSerializer(),
            400: "Parámetros inválidos.",
            403: "Sin permiso.",
            500: "No fue posible leer el log.",
        },
    )
    def get(self, request):
        query = LogAuditoriaQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = query.validated_data
        filtros = {
            "usuario": datos.get("usuario"),
            "accion": datos.get("accion"),
        }

        try:
            consulta = logService.consultar("auditoria", filtros, datos["limite"])
        except LogNoDisponible_500 as error:
            logger.error(f"Lectura de auditoria.log fallida: {error}")
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Consultar la auditoría también queda auditado
        auditar(
            obtener_ip(request), "CONSULTAR_LOG_AUDITORIA", request,
            filtros=consulta.filtros_aplicados or "ninguno",
            resultados=consulta.total
        )

        return Response(LogConsultaSerializer(consulta).data, status=status.HTTP_200_OK)


class LogTecnicoView(APIView):
    """
    GET /api/auth/logs/tecnico/
    Devuelve entradas del log técnico (WARNING, ERROR, CRITICAL).
    Requiere el permiso 'logs.ver_tecnico'.

    Parámetros opcionales:
      ?nivel=ERROR
      ?modulo=views
      ?limite=50          (1 a 1000, por defecto 100)
    """

    permission_classes = [IsAuthenticated, HasPermission]
    permiso_requerido = "logs.ver_tecnico"

    @swagger_auto_schema(
        operation_summary="Consultar el log técnico",
        query_serializer=LogTecnicoQuerySerializer,
        responses={
            200: LogConsultaSerializer(),
            400: "Parámetros inválidos.",
            403: "Sin permiso.",
            500: "No fue posible leer el log.",
        },
    )
    def get(self, request):
        query = LogTecnicoQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = query.validated_data
        filtros = {
            "nivel": datos.get("nivel"),
            "modulo": datos.get("modulo"),
        }

        try:
            consulta = logService.consultar("tecnico", filtros, datos["limite"])
        except LogNoDisponible_500 as error:
            logger.error(f"Lectura de tecnico.log fallida: {error}")
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(LogConsultaSerializer(consulta).data, status=status.HTTP_200_OK)