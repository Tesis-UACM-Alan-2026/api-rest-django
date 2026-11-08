# productos/views.py
import logging
from decimal import Decimal, InvalidOperation
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from gestion_productos.service import ProductoService
from gestion_productos.VO.productoVO import ProductoVO
from gestion_productos.exceptions.productoExceptions import ProductoNoEncontrado_404
from .serializers import (
    ProductoCompletoSerializer,
    ProductoParcialSerializer
)
from rest_framework.permissions import IsAuthenticated
from gestion_permisos.permissions import HasPermission
productoService = ProductoService()
logger = logging.getLogger(__name__)


def obtener_ip(request):
    """Obtiene la dirección IP del cliente."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


class ProductoViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated, HasPermission]
    permisos_requeridos = {
        "list": "productos.ver",
        "retrieve": "productos.ver",
        "search": "productos.ver",
        "filtrar_por_precio": "productos.ver",
        "create": "productos.crear",
        "update": "productos.editar",
        "partial_update": "productos.editar",
        "destroy": "productos.eliminar",
    }

    @swagger_auto_schema(
        operation_summary="Listar productos",
        operation_description="Obtiene todos los productos registrados.",
        responses={200: ProductoCompletoSerializer(many=True)}
    )
    def list(self, request):
        productos_vo = productoService.listar_productos()
        serializer = ProductoCompletoSerializer(productos_vo, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Consultar producto",
        operation_description="Obtiene un producto mediante su ID.",
        responses={
            200: ProductoCompletoSerializer(),
            404: "Producto no encontrado."
        }
    )
    def retrieve(self, request, pk=None):
        try:
            producto_vo = productoService.obtener_producto(pk)
            serializer = ProductoCompletoSerializer(producto_vo)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except ProductoNoEncontrado_404:
            return Response(
                {"error": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_summary="Crear producto",
        operation_description="Registra un producto nuevo.",
        request_body=ProductoCompletoSerializer,
        responses={
            201: ProductoCompletoSerializer(),
            400: "Datos inválidos."
        }
    )
    def create(self, request):
        serializer = ProductoCompletoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto_vo = ProductoVO.desde_dict(serializer.validated_data)
            creado_vo = productoService.crear_producto(producto_vo)

            logger.info(
                "Producto creado. Usuario: %s | IP: %s | Producto ID: %s",
                request.user,
                obtener_ip(request),
                creado_vo.id
            )

            return Response(
                ProductoCompletoSerializer(creado_vo).data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as error:
            return Response(
                error.detail,
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Actualizar producto",
        operation_description="Actualiza todos los campos editables del producto.",
        request_body=ProductoCompletoSerializer,
        responses={
            200: ProductoCompletoSerializer(),
            400: "Datos inválidos.",
            404: "Producto no encontrado."
        }
    )
    def update(self, request, pk=None):
        serializer = ProductoCompletoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto_vo = ProductoVO.desde_dict(serializer.validated_data)
            actualizado_vo = productoService.actualizar_producto(pk, producto_vo)

            logger.info(
                "Producto actualizado. Usuario: %s | IP: %s | Producto ID: %s",
                request.user,
                obtener_ip(request),
                actualizado_vo.id
            )

            return Response(
                ProductoCompletoSerializer(actualizado_vo).data,
                status=status.HTTP_200_OK
            )

        except ProductoNoEncontrado_404:
            return Response(
                {"error": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as error:
            return Response(
                error.detail,
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Actualizar parcialmente un producto",
        operation_description="Modifica solamente los campos enviados.",
        request_body=ProductoParcialSerializer,
        responses={
            200: ProductoCompletoSerializer(),
            400: "Datos inválidos.",
            404: "Producto no encontrado."
        }
    )
    def partial_update(self, request, pk=None):
        serializer = ProductoParcialSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto_vo = ProductoVO.desde_dict(serializer.validated_data)
            actualizado_vo = productoService.actualizar_producto_parcial(pk, producto_vo)

            logger.info(
                "Producto actualizado parcialmente. Usuario: %s | IP: %s | Producto ID: %s",
                request.user,
                obtener_ip(request),
                actualizado_vo.id
            )

            return Response(
                ProductoCompletoSerializer(actualizado_vo).data,
                status=status.HTTP_200_OK
            )

        except ProductoNoEncontrado_404:
            return Response(
                {"error": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as error:
            return Response(
                error.detail,
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Eliminar producto",
        operation_description="Elimina físicamente un producto de la base de datos.",
        responses={
            200: "Producto eliminado correctamente.",
            404: "Producto no encontrado."
        }
    )
    def destroy(self, request, pk=None):
        try:
            productoService.eliminar_producto(pk)

            logger.info(
                "Producto eliminado. Usuario: %s | IP: %s | Producto ID: %s",
                request.user,
                obtener_ip(request),
                pk
            )

            return Response(
                {"mensaje": "Producto eliminado correctamente."},
                status=status.HTTP_200_OK
            )

        except ProductoNoEncontrado_404:
            return Response(
                {"error": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_summary="Buscar productos",
        operation_description="Busca productos por coincidencia en el nombre.",
        manual_parameters=[
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                description="Texto que se desea buscar en el nombre del producto.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: ProductoCompletoSerializer(many=True),
            400: "Debe proporcionar un término de búsqueda."
        }
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response(
                {"error": "Debe proporcionar un término de búsqueda."},
                status=status.HTTP_400_BAD_REQUEST
            )

        productos_vo = productoService.buscar_productos(query)
        serializer = ProductoCompletoSerializer(productos_vo, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Filtrar productos por precio",
        operation_description="Obtiene productos cuyo precio se encuentra dentro del rango indicado.",
        manual_parameters=[
            openapi.Parameter(
                "precio_min",
                openapi.IN_QUERY,
                description="Precio mínimo.",
                type=openapi.TYPE_NUMBER,
                required=True
            ),
            openapi.Parameter(
                "precio_max",
                openapi.IN_QUERY,
                description="Precio máximo.",
                type=openapi.TYPE_NUMBER,
                required=True
            )
        ],
        responses={
            200: ProductoCompletoSerializer(many=True),
            400: "Rango de precios inválido."
        }
    )
    @action(detail=False, methods=["get"], url_path="filtrar-precio")
    def filtrar_por_precio(self, request):
        precio_min = request.query_params.get("precio_min")
        precio_max = request.query_params.get("precio_max")

        if precio_min is None or precio_max is None:
            return Response(
                {"error": "Debe proporcionar precio_min y precio_max."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            precio_min = Decimal(precio_min)
            precio_max = Decimal(precio_max)

            if not precio_min.is_finite() or not precio_max.is_finite():
                raise InvalidOperation

            if precio_min < 0 or precio_max < 0:
                raise ValueError

            if precio_min > precio_max:
                return Response(
                    {"error": "El precio mínimo no puede ser mayor que el precio máximo."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except (InvalidOperation, ValueError, TypeError):
            return Response(
                {"error": "Los precios deben ser valores numéricos válidos y no negativos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        productos_vo = productoService.filtrar_por_rango_precio(precio_min, precio_max)
        serializer = ProductoCompletoSerializer(productos_vo, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)