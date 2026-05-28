"""
Vista API para listar usuarios registrados.

Incluye:
- Filtros exactos (filterset_fields)
- Búsqueda parcial (search_fields)
- Ordenamiento (ordering_fields)
- Documentación OpenAPI
- Paginación automática si está habilitada
"""

import logging
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework import status, filters, generics
from drf_yasg.utils import swagger_auto_schema
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from core.responses import get_list_success_response
from core.pagination import Pagination
from core.responses import success_response, error_response
from user import messages
from user.models import User
from user.serializers import ViewUser
from http import HTTPStatus
import time

import time
from datetime import datetime
logger = logging.getLogger(__name__)


class UserListView(generics.ListAPIView):
    """
    Lista todos los usuarios registrados en el sistema.

    Endpoint:
        GET /api/users/

    Requiere:
        - Autenticación.
        - Permisos adecuados (basados en modelo).

    Características:
        - Paginación automática (si está habilitada en settings).
        - Filtros, búsqueda y ordenamiento desde query parameters.
        - Uso de `success_response` para respuestas uniformes.
        - Logging para trazabilidad.
    """

    queryset = User.objects.all()
    serializer_class = ViewUser
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    pagination_class = Pagination

    # Opcional: agregar filtros, ordenamiento o búsqueda
    # Indica qué tipos de filtros están habilitado
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Define qué campos pueden usarse para filtros exactos con DjangoFilterBackend.
    # Ejemplos de uso en la URL:/api/users/?email=ejemplo@correo.com
    filterset_fields = ['is_active', 'is_deleted','is_superuser', 'email_verified']
    # Define en qué campos se puede hacer búsqueda textual parcial con SearchFilter.
    # Ejemplo de uso: /api/users/?search=gmail
    search_fields = ['email']
    # Define por qué campos se puede ordenar la lista de resultados.
    # Ejemplos de uso: /api/users/?ordering=email -> ordena ascendente por email
    # /api/users/?ordering=-created_at -> ordena descendente por fecha de creación
    ordering_fields = ['created_at', 'email']

    def order(self):
        queryset = super().get_queryset()
        sort = self.request.query_params.get('sort')
        order = self.request.query_params.get('order', 'asc')

        if sort:
            ordering = f"-{sort}" if order == 'desc' else sort
            queryset = queryset.order_by(ordering)

        return queryset
    

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Obtiene una lista paginada de todos los usuarios registrados en el sistema. Este endpoint está restringido a usuarios con permisos administrativos. Incluye información personal, laboral y de auditoría de cada usuario"
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    def list(self, request, *args, **kwargs):
        logger.info(f"Solicitud de listado de usuarios por {request.user.email}")
        
        initial_time = time.time() * 1000
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            pagination_data = {
                "page": self.paginator.page.number,
                "perPage": self.paginator.get_page_size(request),
                "totalPages": self.paginator.page.paginator.num_pages,
                "totalItems": self.paginator.page.paginator.count
            }

            final_time = time.time() * 1000
            execution_time_ms = final_time - initial_time

            return get_list_success_response(
                status_code=HTTPStatus.OK,
                execution_time_ms=execution_time_ms,
                request=request,
                response_message=paginated_response.data.get('results', serializer.data),
                pagination=pagination_data
            )

        serializer = self.get_serializer(queryset, many=True)
        final_time = time.time() * 1000
        execution_time_ms = final_time - initial_time

        return get_list_success_response(
            status_code=HTTPStatus.OK,
            execution_time_ms=execution_time_ms,
            request=request,
            response_message=serializer.data,
            pagination=None
        )
