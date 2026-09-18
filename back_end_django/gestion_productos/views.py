#codigo8##########################################3
import logging
from django.shortcuts import render

# Create your views here.
# gestion_productos/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from gestion_productos.DAO.productoDAO import ProductoDAO
from .serializers import ProductoCompletoSerializer, ProductoParcialSerializer
from gestion_productos.serializers import ProductoCompletoSerializer, ProductoParcialSerializer
from gestion_productos.exceptions.productoExceptions import (
    DatosInvalidos_400,
    ProductoNoEncontrado_404,
    ConflictoProducto_409,
    ErrorInternoServidor_500,
    ProductoNoAutorizado_401,
    ProductoProhibido_403,
)
logger = logging.getLogger('gestion_productos') #técnicos 
logger_auditoria = logging.getLogger('auditoria') #auditoria

def obtener_ip(request): #NUEVO
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'IP desconocida')

class ProductoViewSet(viewsets.ViewSet):
    """
    API para la gestión de Productos.
    """

    @swagger_auto_schema(
        operation_summary="Obtener todos los productos",
        responses={
            200: "Éxito",
            401: "No autorizado",
            403: "Prohibido",
            500: "Error interno del servidor",
        },
    )
    def list(self, request, *args, **kwargs):
        """Devuelve una lista de todos los productos con soporte para paginación, ordenamiento y filtrado."""
        
        try:
            logger.debug("Obteniendo lista de productos") #NUEVO
            productos = ProductoDAO.obtener_todos()
            serializer = ProductoCompletoSerializer(productos, many=True)
            logger.info(f"Lista de productos obtenida exitosamente. Total: {len(productos)}") #NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ProductoNoAutorizado_401 as e:
            logger.warning(f"Acceso no autorizado a la lista de productos: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except ProductoProhibido_403 as e:
            logger.warning(f"Acceso prohibido a la lista de productos: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al obtener la lista de productos: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#############codigo10#########################################3
    @swagger_auto_schema(
        operation_summary="Obtener un producto por ID",
        responses={
            200: "Éxito",
            401: "No Autorizado",
            403: "Prohibido",
            404: "Producto no encontrado",
            500: "Error interno del servidor",
        },
    )
    def retrieve(self, request, pk=None):
        """Obtiene los detalles de un producto específico utilizando su ID."""
        try:
            logger.debug(f"Obteniendo producto con ID: {pk}") #NUEVO
            producto = ProductoDAO.obtener_producto_por_id(pk)
            serializer = ProductoCompletoSerializer(producto)
            logger.info(f"Producto con ID {pk} obtenido exitosamente") #NUEVO
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ProductoNoAutorizado_401 as e:
            logger.warning(f"Acceso no autorizado al obtener producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except ProductoProhibido_403 as e:
            logger.warning(f"Acceso prohibido al obtener producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al obtener producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #####################Codigo 12##########################################
    @swagger_auto_schema(
        operation_summary="Crear un nuevo producto",
        request_body=ProductoCompletoSerializer,
        responses={
            201: "Producto creado exitosamente",
            400: "Error en la validación",
            409: "Conflicto (product_key ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def create(self, request):
        """Crea un nuevo producto con la información proporcionada en el cuerpo de la petición."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando crear un nuevo producto con data: {request.data}") #NUEVO
            producto = ProductoDAO.crear_producto(**request.data)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:CREAR_PRODUCTO] "
                f"[ realizado_por :{ request .user }]"
                f"[ product_key :{ request .data.get(' product_key ')}]"
            )
            return Response(
                ProductoCompletoSerializer(producto).data,
                status=status.HTTP_201_CREATED
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al crear producto: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ConflictoProducto_409 as e:
            logger.warning(f"Conflicto al crear producto (product_key ya registrado): {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al crear producto: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
############Codigo 14##########################################
    @swagger_auto_schema(
        operation_summary="Actualizar un producto (completo)",
        request_body=ProductoCompletoSerializer,
        responses={
            200: "Producto actualizado exitosamente",
            400: "Datos inválidos",
            404: "Producto no encontrado",
            409: "Conflicto (product_key ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def update(self, request, pk=None):
        """Actualiza completamente un producto especificado por su ID."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando actualizar producto con ID {pk} y data: {request.data}") #NUEVO
            productoDTO = ProductoDAO.actualizar_producto(pk, **request.data)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_PRODUCTO] "
                f"[ realizado_por :{ request .user }] [ id_actualizado :{pk}]"
            )
            return Response(
                ProductoCompletoSerializer(productoDTO).data,
                status=status.HTTP_200_OK
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al actualizar producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para actualizar con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoProducto_409 as e:
            logger.warning(f"Conflicto al actualizar producto con ID {pk} (product_key ya registrado): {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al actualizar producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
############################Codigo 16##########################################
    @swagger_auto_schema(
        operation_summary="Actualizar un producto (parcialmente)",
        request_body=ProductoParcialSerializer,
        responses={
            200: "Producto actualizado parcialmente",
            400: "Datos inválidos",
            404: "Producto no encontrado",
            409: "Conflicto (product_key ya registrado)",
            500: "Error interno del servidor",
        },
    )
    def partial_update(self, request, pk=None):
        """Actualiza parcialmente un producto especificado por su ID."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando actualizar producto parcialmente con ID {pk} y data: {request.data}") #NUEVO
            productoDTO = ProductoDAO.actualizar_producto_parcial(pk, **request.data)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_PRODUCTO_PARCIAL] "
                f"[ realizado_por :{ request .user }] [ id_actualizado :{pk}]"
            )
            return Response(
                ProductoParcialSerializer(productoDTO).data,
                status=status.HTTP_200_OK
            )

        except DatosInvalidos_400 as e:
            logger.warning(f"Error de validación al actualizar producto parcialmente con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para actualizar parcialmente con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ConflictoProducto_409 as e:
            logger.warning(f"Conflicto al actualizar producto parcialmente con ID {pk} (product_key ya registrado): {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        except ErrorInternoServidor_500 as e:
            logger.error(f"Error interno al actualizar producto parcialmente con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
################################Codigo 18##########################################
    @swagger_auto_schema(
        operation_summary="Elimina un producto (borrado lógico).",
        responses={
            200: "Producto eliminado correctamente",
            401: "No autorizado",
            400: "Error en la validación",
            404: "Producto no encontrado",
        },
    )
    def destroy(self, request, pk=None):
        """Marca el producto como eliminado sin borrarlo físicamente."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando eliminar producto con ID {pk}") #NUEVO
            ProductoDAO.eliminar_producto(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ELIMINAR_PRODUCTO] "
                f"[ realizado_por :{ request .user }] [ id_eliminado :{pk}]"
            )
            return Response(
                {"mensaje": "Producto eliminado correctamente"},
                status=status.HTTP_200_OK
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para eliminar con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Error de validación al intentar eliminar producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
####################################Codigo 20##########################################

    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Restaurar un producto eliminado.",
        responses={
            200: "Producto restaurado exitosamente",
            401: "No autorizado",
            400: "El producto no estaba eliminado",
            404: "Producto no encontrado",
        },
    )
    def restore(self, request, pk=None):
        """Restaura un producto eliminado lógicamente."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando restaurar producto con ID {pk}") #NUEVO
            ProductoDAO.restaurar_producto(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:RESTAURAR_PRODUCTO] "
                f"[ realizado_por :{ request .user }] [ id_restaurado :{pk}]"
            )
            return Response(
                {"mensaje": "Producto restaurado correctamente"},
                status=status.HTTP_200_OK
            )

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para restaurar con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            logger.warning(f"Error de validación al intentar restaurar producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#####################################Codigo 22##########################################
    @action(detail=False, methods=["get"], url_path="search")
    @swagger_auto_schema(
        operation_summary="Buscar productos por nombre o descripción",
        manual_parameters=[
            openapi.Parameter(
                "q", openapi.IN_QUERY,
                description="Texto a buscar en nombre o descripción",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: ProductoCompletoSerializer(many=True),
            400: "Consulta de búsqueda inválida",
            401: "No autorizado",
            403: "Prohibido",
            404: "No se encontraron productos",
            500: "Error interno del servidor"
        }
    )
    def search(self, request):
        query = request.GET.get("q", "")
        if not query:
            logger.warning("Consulta de búsqueda inválida: parámetro 'q' no proporcionado") #NUEVO
            return Response(
                {"error": "Debe proporcionar un parámetro de búsqueda"},
                status=status.HTTP_400_BAD_REQUEST
            )
        logger.debug(f"Buscando productos con query: {query}") #NUEVO
        productos = ProductoDAO.buscar_productos(query)
        serializer = ProductoCompletoSerializer(productos, many=True)
        logger .info(f" Búsqueda '{query}' devolvió {len( serializer .data)} resultados") #NUEVO
        return Response(serializer.data, status=status.HTTP_200_OK)
###############################Codigo 24##########################################
    @action(detail=False, methods=["get"], url_path="filtrar-precio")
    @swagger_auto_schema(
        operation_summary="Filtrar productos por rango de precio",
        manual_parameters=[
            openapi.Parameter(
                "precio_min",
                openapi.IN_QUERY,
                description="Precio mínimo",
                type=openapi.TYPE_NUMBER,
                required=True,
            ),
            openapi.Parameter(
                "precio_max",
                openapi.IN_QUERY,
                description="Precio máximo",
                type=openapi.TYPE_NUMBER,
                required=True,
            ),
        ],
        responses={
            200: "Éxito",
            400: "Parámetros inválidos",
            500: "Error interno del servidor",
        },
    )
    def filtrar_por_precio(self, request):
        """
        Filtra productos por rango de precio.
        """

        try:
            precio_min = request.query_params.get("precio_min")
            precio_max = request.query_params.get("precio_max")

            if precio_min is None or precio_max is None:
                logger.warning("Parámetros de precio inválidos: precio_min o precio_max no proporcionados") #NUEVO
                return Response(
                    {
                        "error": "Debe proporcionar precio_min y precio_max"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            productos = ProductoDAO.filtrar_por_rango_precio(
                precio_min,
                precio_max,
            )
            logger.info(f"Filtrado por precio entre {precio_min} y {precio_max} devolvió {len(productos)} productos") #NUEVO

            serializer = ProductoCompletoSerializer(
                productos,
                many=True,
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error inesperado al filtrar productos por precio: {str(e)}") #NUEVO
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
##################################Codigo 26##########################################
    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Actualizar imagen de producto",
        manual_parameters=[
            openapi.Parameter(
                "image_link", openapi.IN_QUERY,
                description="string (URL válida , máximo 200 caracteres)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: "Imagen actualizada exitosamente",
            400: "URL inválida o excede el límite de caracteres",
            404: "Producto no encontrado",
            500: "Error interno del servidor"
        }
    )
    def update_image(self, request, pk=None):
        """Actualiza la URL de la imagen de un producto específico."""
        ip = obtener_ip(request) #NUEVO
        try:
            img = request.GET.get("image_link", "")
            logger.debug(f"Intentando actualizar imagen del producto con ID {pk} a URL: {img}") #NUEVO
            producto = ProductoDAO.actualizar_img(pk, img)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTUALIZAR_IMAGEN_PRODUCTO] "
                f"[ realizado_por :{ request .user }] [ id_actualizado :{pk}]"
            )

            data = {
                "codigo": 200,
                "mensaje": "Imagen del producto actualizada exitosamente.",
                "resultado": {
                    "id": str(producto.id),
                    "image_link": producto.image_link,
                    "modified_at": producto.modified_at.isoformat()
                }
            }
            return Response(data, status=status.HTTP_200_OK)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para actualizar imagen con ID {pk}: {str(e)}") #NUEVO
            data = {"codigo": 404, "mensaje": "Producto no encontrado.", "resultado": "null"}
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        except ValidationError:
            logger.warning(f"Error de validación al intentar actualizar imagen del producto con ID {pk}: {str(e)}") #NUEVO
            data = {
                "codigo": 400,
                "mensaje": "La URL de la imagen no es válida o excede el límite de caracteres.",
                "resultado": "null"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error inesperado al intentar actualizar imagen del producto con ID {pk}: {str(e)}") #NUEVO
            data = {
                "codigo": 500,
                "mensaje": "Error interno del servidor al actualizar la imagen.",
                "resultado": "null"
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
##################################Codigo 28##########################################
    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Desactivar un producto",
        responses={
            200: "Producto desactivado exitosamente",
            401: "No autorizado",
            400: "El producto ya estaba desactivado",
            403: "Prohibido",
            404: "Producto no encontrado",
            500: "Error interno del servidor"
        }
    )
    def deactivate(self, request, pk=None):
        """Desactiva un producto estableciendo el campo status en false."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando desactivar producto con ID {pk}") #NUEVO
            producto = ProductoDAO.desactivar_producto(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:DESACTIVAR_PRODUCTO] "
                f"[ realizado_por :{ request .user }] [ id_desactivado :{pk}]"
            )
            data = {
                "codigo": 200,
                "mensaje": "Producto desactivado exitosamente.",
                "resultado": {
                    "id": str(producto.id),
                    "status": producto.status,
                    "modified_at": producto.modified_at.isoformat()
                }
            }
            return Response(data, status=status.HTTP_200_OK)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para desactivar con ID {pk}: {str(e)}") #NUEVO
            return Response({"codigo": 404, "mensaje": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            logger.warning(f"Error de validación al intentar desactivar producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"codigo": 400, "mensaje": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error inesperado al intentar desactivar producto con ID {pk}: {str(e)}") #NUEVO
            return Response(
                {"codigo": 500, "mensaje": "Error interno del servidor", "detalle": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
##############################Codigo 30##########################################
    @action(detail=True, methods=["patch"])
    @swagger_auto_schema(
        operation_summary="Activar un producto",
        responses={
            200: "Producto activado correctamente",
            401: "No autorizado",
            400: "El producto ya estaba activado",
            404: "Producto no encontrado"
        }
    )
    def activate(self, request, pk=None):
        """Activa un producto estableciendo el campo status en true."""
        ip = obtener_ip(request) #NUEVO
        try:
            logger.debug(f"Intentando activar producto con ID {pk}") #NUEVO
            ProductoDAO.activar_producto(pk)
            logger_auditoria.info( #NUEVO
                f"ip:{ip}] [accion:ACTIVAR_PRODUCTO] "
                f"[ realizado_por :{ request .user }] [ id_activado :{pk}]"
            )
            return Response({"mensaje": "Producto activado correctamente"}, status=status.HTTP_200_OK)

        except ProductoNoEncontrado_404 as e:
            logger.warning(f"Producto no encontrado para activar con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            logger.warning(f"Error de validación al intentar activar producto con ID {pk}: {str(e)}") #NUEVO
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        