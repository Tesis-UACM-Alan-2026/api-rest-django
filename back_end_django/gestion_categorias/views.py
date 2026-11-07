import logging

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from gestion_permisos.permissions import HasPermission
from gestion_categorias.service import CategoriaService
from gestion_categorias.VO.categoriaVO import CategoriaVO
from gestion_categorias.exceptions.categoriaExceptions import (
    CategoriaNoEncontrada_404,
    CategoriaDuplicada_409,
    CategoriaConProductos_409,
)
from .serializers import CategoriaSerializer

categoriaService = CategoriaService()
logger = logging.getLogger(__name__)


def obtener_ip(request):
    """Obtiene la dirección IP del cliente."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


class CategoriasViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated, HasPermission]
    permisos_requeridos = {
        "list": "categorias.ver",
        "retrieve": "categorias.ver",
        "create": "categorias.crear",
        "update": "categorias.editar",
        "partial_update": "categorias.editar",
        "destroy": "categorias.eliminar",
    }

    @swagger_auto_schema(
        operation_summary="Listar categorías",
        operation_description="Obtiene todas las categorías registradas.",
        responses={
            200: CategoriaSerializer(many=True)
        }
    )
    def list(self, request):
        categorias_vo = categoriaService.listar_categorias()
        serializer = CategoriaSerializer(categorias_vo, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Consultar categoría",
        operation_description="Obtiene una categoría mediante su identificador.",
        responses={
            200: CategoriaSerializer(),
            404: "Categoría no encontrada."
        }
    )
    def retrieve(self, request, pk=None):
        try:
            categoria_vo = categoriaService.obtener_categoria(pk)
            serializer = CategoriaSerializer(categoria_vo)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except CategoriaNoEncontrada_404 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_summary="Crear categoría",
        operation_description="Registra una nueva categoría.",
        request_body=CategoriaSerializer,
        responses={
            201: CategoriaSerializer(),
            400: "Datos inválidos.",
            409: "Ya existe una categoría con ese nombre."
        }
    )
    def create(self, request):
        serializer = CategoriaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            categoria_vo = CategoriaVO.desde_dict(serializer.validated_data)
            creada_vo = categoriaService.crear_categoria(categoria_vo)

            logger.info(
                "Categoría creada. Usuario: %s | IP: %s | Categoría ID: %s",
                request.user,
                obtener_ip(request),
                creada_vo.id
            )

            return Response(
                CategoriaSerializer(creada_vo).data,
                status=status.HTTP_201_CREATED
            )

        except CategoriaDuplicada_409 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_409_CONFLICT
            )

    @swagger_auto_schema(
        operation_summary="Actualizar categoría",
        operation_description="Actualiza todos los datos de una categoría.",
        request_body=CategoriaSerializer,
        responses={
            200: CategoriaSerializer(),
            400: "Datos inválidos.",
            404: "Categoría no encontrada.",
            409: "Ya existe una categoría con ese nombre."
        }
    )
    def update(self, request, pk=None):
        serializer = CategoriaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            categoria_vo = CategoriaVO.desde_dict(serializer.validated_data)
            actualizada_vo = categoriaService.actualizar_categoria(pk, categoria_vo)

            logger.info(
                "Categoría actualizada. Usuario: %s | IP: %s | Categoría ID: %s",
                request.user,
                obtener_ip(request),
                actualizada_vo.id
            )

            return Response(
                CategoriaSerializer(actualizada_vo).data,
                status=status.HTTP_200_OK
            )

        except CategoriaNoEncontrada_404 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_404_NOT_FOUND
            )

        except CategoriaDuplicada_409 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_409_CONFLICT
            )

    @swagger_auto_schema(
        operation_summary="Actualizar parcialmente una categoría",
        operation_description="Modifica únicamente los campos proporcionados.",
        request_body=CategoriaSerializer,
        responses={
            200: CategoriaSerializer(),
            400: "Datos inválidos.",
            404: "Categoría no encontrada.",
            409: "Ya existe una categoría con ese nombre."
        }
    )
    def partial_update(self, request, pk=None):
        serializer = CategoriaSerializer(data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            categoria_vo = CategoriaVO.desde_dict(serializer.validated_data)
            actualizada_vo = categoriaService.actualizar_categoria_parcial(pk, categoria_vo)

            logger.info(
                "Categoría actualizada parcialmente. Usuario: %s | IP: %s | Categoría ID: %s",
                request.user,
                obtener_ip(request),
                actualizada_vo.id
            )

            return Response(
                CategoriaSerializer(actualizada_vo).data,
                status=status.HTTP_200_OK
            )

        except CategoriaNoEncontrada_404 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_404_NOT_FOUND
            )

        except CategoriaDuplicada_409 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_409_CONFLICT
            )

    @swagger_auto_schema(
        operation_summary="Eliminar categoría",
        operation_description=(
                "Elimina una categoría. No se permite eliminarla "
                "si tiene productos asociados."
        ),
        responses={
            200: "Categoría eliminada correctamente.",
            404: "Categoría no encontrada.",
            409: "La categoría tiene productos asociados."
        }
    )
    def destroy(self, request, pk=None):
        try:
            categoriaService.eliminar_categoria(pk)

            logger.info(
                "Categoría eliminada. Usuario: %s | IP: %s | Categoría ID: %s",
                request.user,
                obtener_ip(request),
                pk
            )

            return Response(
                {"mensaje": "Categoría eliminada correctamente."},
                status=status.HTTP_200_OK
            )

        except CategoriaNoEncontrada_404 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_404_NOT_FOUND
            )

        except CategoriaConProductos_409 as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_409_CONFLICT
            )