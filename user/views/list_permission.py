"""
    Permite desbloquear un usuario ver una lista de permisos en el sistema.
    Este endpoint requiere permisos especiales para poder ejecutarse.

    Endpoint:

        GET /users/permissions

    Parametros:
        - user_id: UUID del usuario a bloquear

    Retorna:
        - 200 OK si fue exitoso y la lista de permisos
        - 401 Not Found no tiene las credenciales necesarias
        - 500 Internal Server Error si ocurre un error inesperado
    """

from http import HTTPStatus
import logging
from venv import logger
from django.contrib.auth.models import Permission

from core.responses import error_response, success_response
from user import messages
from user.serializers import ListPermissionSerializer
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, filters, generics
from django_filters.rest_framework import DjangoFilterBackend  
from datetime import datetime
import time

from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter


logger = logging.getLogger(__name__)

"""
La Clase TenResultsPagination es una propuesta a la necesidad de tener paginación en 
nuestra endpoint. 

Los atributos que tienen son:
    - page_size Definir El número de elementos por defecto
    - page_size_query_param Esto hace que podamos editarlo el numero de elementos por pag. 
    - max_page_size Esto proteje el número de elementos maximo que podemos pedir por pag.
"""
class TenResultsPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size' 
    max_page_size = 100



class PermissionListView(generics.ListAPIView):
    """
        Lista todos los pemisos registrados en el sistema.

        Endpoint:
            GET /users/permissions

        Requiere:
            - Autenticación.
            - Permisos adecuados (basados en modelo).

        Características:
            - Paginación automática (si está habilitada en settings).
            - Filtros, búsqueda y ordenamiento desde query parameters.
            - Uso de `success_response` para respuestas uniformes.
    """
  
    queryset = Permission.objects.all()
    serializer_class = ListPermissionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    pagination_class = TenResultsPagination

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    #Campos con los que se puedan ordenar
    ordering_fields = ['id','name']  
    ordering = ['id'] 
    

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Consumo para obtener la lista de los Permisos en el Sistema."
    )
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        
        logger.info(f"Solicitud de listado de permisos por {request.user.email}")
        
        #Iniciamos la medición del tiempo iniciando al comenzar la solicitud.
        start_time = time.time()
        try:
            print("Permisos de usuario:", request.user.get_all_permissions())
            # Verificamos si el usuario autenticado tiene permiso para listar permisos.
            if not (request.user.has_perm("user.can_manage_permissions")):
                logger.warning(f"Usuario sin permisos intentó listar permisos en el sistema: {request.user.email}")
                return error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message=messages.INSUFFICIENT_PERMISSIONS
                )

            """
                Para poder utilizar el paginador necesitamos separara el queryset y page
                para poder acceder a las paginas y así mandar la información al usuario.
            """
            # Aplicar filtros si están configurados
            queryset = self.filter_queryset(self.get_queryset())
            # Aplica la paginación y guarda la página activa
            page = self.paginate_queryset(queryset)
            #verificamos que exista información de la paginación
            if page is not None:
                serializer = self.get_serializer(page, many=True)

                pagination_info = {
                    "page": self.paginator.page.number,
                    "perPage": self.paginator.get_page_size(request),
                    "totalPages": self.paginator.page.paginator.num_pages,
                    "totalItems": self.paginator.page.paginator.count,
                }

            else:
                pagination_info = {
                    "page": None,
                    "perPage": None,
                    "totalPages": None,
                    "totalItems": None,
                }
            
            end_time = time.time()
            executionTimeMs = int((end_time - start_time) * 1000)

            

            response_message = {
                    "message": messages.PERMISSION_LIST_SUCCESS,
                    "data": serializer.data,
                    "pagination": pagination_info
                    }

            return success_response(
                status_code= status.HTTP_200_OK,
                execution_time_ms= executionTimeMs,
                request= request,
                response= response_message
                
            )	
        except Exception as e:
            logger.error( messages.PERMISSION_LIST_ERROR + f": {e}", exc_info=True)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message= messages.UNKNOWN_ERROR
            )
