from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from .models import Categoria
from .serializers import CategoriaSerializer


class CategoriasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para administrar las categorías de productos.
    """

    queryset = Categoria.objects.all().order_by("id")
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Obtiene el listado de todas las categorías."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Registra una nueva categoría."
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Obtiene una categoría mediante su identificador."
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualiza todos los datos de una categoría."
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualiza parcialmente una categoría."
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Elimina una categoría mediante su identificador."
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)