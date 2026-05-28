"""
Vista API para listar usuarios registrados.

Incluye:
- Filtros exactos (filterset_fields)
- Búsqueda parcial (search_fields)
- Ordenamiento (ordering_fields)
- Documentación OpenAPI
- Paginación automática si está habilitada
"""
from django.contrib.auth.models import Group
import logging
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework import status, filters, generics
from drf_yasg.utils import swagger_auto_schema
from django_filters.rest_framework import DjangoFilterBackend

from core.responses import success_response, error_response
from user import messages
import time 
from user.serializers.roles_serializer import RoleListSerializer 
from core.pagination import Pagination


logger = logging.getLogger(__name__)

class RolesListView(generics.ListAPIView):
    """
        Lista todos los roles registrados en el sistema

        Endpoint:
            GET /api/users/roles
        Requiere:
            - Autenticación
            - Permisos adecuados (basados en el modelo)
        Características:
            - Paginación automática (si está habilitada en settings).
            - Filtros, búsqueda y ordenamiento desde query parameters.
            - Uso de `success_response` para respuestas uniformes.
            - Logging para trazabilidad.    
    """
    queryset=Group.objects.all()
    permission_classes=[IsAuthenticated,DjangoModelPermissions]
    serializer_class=RoleListSerializer
    pagination_class = Pagination
    
    # Requerido: Agregar filtros 
    # Filtros
    #  - Paginacion: numero de pagina actual
    #  - PerPage: Numero de elementops por pagina (por defecto 10)
    #  - sort: Campo por el cual seran ordenados
    #  - ordenamiento: orden ascendente o descendente
    # Indica que tipos de filtros estan habilitados
    filter_backends = [DjangoFilterBackend,filters.OrderingFilter,]
    ordering_fields = ['id', 'name']  # Campos permitidos para ordenar
    ordering = ['id'] # Ordenamiento por defecto

    @swagger_auto_schema( 
        tags=["Roles"],
        operation_summary="Lista los roles del sistema",
        operation_description="Consumo para obtener todos los roles definidos en el sistema",
        responses={
            200:"Solicitud exitosa",
            201:"Roles listados exitosamente",
            400:"Solicitud mal formada",
            401:"No autenticado",
            403:"Sin permisos",
            404:"No encontrado",
            500:"Error interno"
        }
            
    )
    def get(self,request,*args,**kwargs):
        """
        Lista todos los roles del sistema
        Args:  
            request (HTTPRequest): Objeto de solicitud HTTP
            page(queryParameter): Entero que indica la página de datos a devolver(por defecto value=1)
            perPage(queryParameter): Entero que indica la cantidad de datos por página a devolver(por defecto value=10)
            ordering(queryParameter): Campo que indica el valor por el cual se ordenan los datos(por defecto value=id)
        Returns:
            200: Respuesta exitosa
            401: sin autorizacion
            400: solicitud mal formada
            403: No tiene los permisos requeridos
            404: No se encontro el recurso
            500: Error interno
        """
        start_time=time.time()
        if not (request.user.has_perm("auth.can_manage_roles")):
            logger.info(f"{request.user.email} no tienes permiso para acceder a los roles del sistema")
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message=messages.INSUFFICIENT_PERMISSIONS
            )

        
        # Se fuerzan los valores por defecto page=1, perPage=10 en caso de que no sean mandados por el usuario
        if 'page' not in request.query_params :
            request.query_params._mutable = True
            request.query_params['page'] = '1'
            request.query_params._mutable = False
        if  'perPage' not in request.query_params :
            request.query_params._mutable = True
            request.query_params['perPage'] = str(self.pagination_class.max_page_size)
            request.query_params._mutable = False
        
        try:
            
            
            logger.info(f"Solicitud de listado de usuarios por {request.user.email}")
            ordering_param= request.query_params.get('ordering')

            if ordering_param:
                # Valida que el campo de ordenamiento sea permitido
                valid_fields = ['id', 'name', '-id', '-name']
                if ordering_param not in valid_fields:
                    return error_response(
                        
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message={"error": f"Campo de ordenamiento inválido. Use: {', '.join(valid_fields)}"},
                        )       


            queryset_result=super().list(request,*args,**kwargs)
            end_time=time.time()
            execution_time= int((end_time - start_time) * 1000)
            
            
                      
            current_page = self.paginator.page.number
            per_page = self.paginator.page.paginator.per_page
            total_pages = self.paginator.page.paginator.num_pages
            total_items = self.paginator.page.paginator.count
            query_data=queryset_result.data['results']
            
                
            return success_response(
                status_code=status.HTTP_200_OK,
                execution_time_ms=execution_time,
                request=request,
                response={
                    "message":"Roles listados exitosamente",
                    "data":query_data,
                    "pagination":{
                        "page": int(current_page),  # Usamos el valor real del paginador
                        "perPage": int(per_page),   # No request.query_params para evitar inconsistencias
                        "totalPages": total_pages,
                        "totalItems": total_items
                    }
                }

            )

        except Exception as e:
            logger.error(f"Error al listar roles: {e}", exc_info=True)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message=messages.INTERNAL_SERVER_ERROR
            )

