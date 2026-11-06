from django.db.models.deletion import ProtectedError

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from gestion_categorias.DAO.categoriaDAO import CategoriaDAO
from .serializers import CategoriaSerializer


class CategoriasViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Listar categorías",
        operation_description="Obtiene todas las categorías registradas.",
        responses={
            200: CategoriaSerializer(many=True)
        }
    )
    def list(self, request):
        categorias = CategoriaDAO.obtener_todas()
        serializer = CategoriaSerializer(categorias, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

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
            categoria = CategoriaDAO.obtener_por_id(pk)
            serializer = CategoriaSerializer(categoria)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        except Exception as error:
            from rest_framework.exceptions import NotFound

            if isinstance(error, NotFound):
                return Response(
                    {"error": str(error.detail)},
                    status=status.HTTP_404_NOT_FOUND
                )

            raise

    @swagger_auto_schema(
        operation_summary="Crear categoría",
        operation_description="Registra una nueva categoría.",
        request_body=CategoriaSerializer,
        responses={
            201: CategoriaSerializer(),
            400: "Datos inválidos."
        }
    )
    def create(self, request):
        serializer = CategoriaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        categoria = CategoriaDAO.crear_categoria(
            **serializer.validated_data
        )

        respuesta = CategoriaSerializer(categoria)

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_summary="Actualizar categoría",
        operation_description="Actualiza todos los datos de una categoría.",
        request_body=CategoriaSerializer,
        responses={
            200: CategoriaSerializer(),
            400: "Datos inválidos.",
            404: "Categoría no encontrada."
        }
    )
    def update(self, request, pk=None):
        try:
            categoria = CategoriaDAO.obtener_por_id(pk)

            serializer = CategoriaSerializer(
                instance=categoria,
                data=request.data
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            categoria = CategoriaDAO.actualizar_categoria(
                pk,
                **serializer.validated_data
            )

            respuesta = CategoriaSerializer(categoria)

            return Response(
                respuesta.data,
                status=status.HTTP_200_OK
            )

        except Exception as error:
            from rest_framework.exceptions import NotFound

            if isinstance(error, NotFound):
                return Response(
                    {"error": str(error.detail)},
                    status=status.HTTP_404_NOT_FOUND
                )

            raise

    @swagger_auto_schema(
        operation_summary="Actualizar parcialmente una categoría",
        operation_description="Modifica únicamente los campos proporcionados.",
        request_body=CategoriaSerializer,
        responses={
            200: CategoriaSerializer(),
            400: "Datos inválidos.",
            404: "Categoría no encontrada."
        }
    )
    def partial_update(self, request, pk=None):
        try:
            categoria = CategoriaDAO.obtener_por_id(pk)

            serializer = CategoriaSerializer(
                instance=categoria,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            categoria = CategoriaDAO.actualizar_categoria_parcial(
                pk,
                **serializer.validated_data
            )

            respuesta = CategoriaSerializer(categoria)

            return Response(
                respuesta.data,
                status=status.HTTP_200_OK
            )

        except Exception as error:
            from rest_framework.exceptions import NotFound

            if isinstance(error, NotFound):
                return Response(
                    {"error": str(error.detail)},
                    status=status.HTTP_404_NOT_FOUND
                )

            raise

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
            CategoriaDAO.eliminar_categoria(pk)

            return Response(
                {"mensaje": "Categoría eliminada correctamente."},
                status=status.HTTP_200_OK
            )

        except ProtectedError:
            return Response(
                {
                    "error": (
                        "No se puede eliminar la categoría porque "
                        "tiene productos asociados."
                    )
                },
                status=status.HTTP_409_CONFLICT
            )

        except Exception as error:
            from rest_framework.exceptions import NotFound

            if isinstance(error, NotFound):
                return Response(
                    {"error": str(error.detail)},
                    status=status.HTTP_404_NOT_FOUND
                )

            raise