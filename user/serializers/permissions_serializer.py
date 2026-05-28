"""
Serializadores para la gestión de permisos y asignación de roles.

Este módulo define los serializadores necesarios para validar las solicitudes
relacionadas con la creación de permisos dinámicos y su asignación a grupos (roles).

Estructura:
- `PermissionCreateSerializer`: Valida los datos requeridos para crear un nuevo permiso.
- `AssignPermissionToGroupSerializer`: Valida la asignación de múltiples permisos a un grupo.

Se utiliza en vistas específicas bajo `views/permissions.py` y mejora la documentación
automática en Swagger mediante `@swagger_auto_schema`.

Autor: [Tu nombre o equipo de desarrollo]
Fecha: [Ultima modificación: 23-jul-25]
"""

from rest_framework import serializers
from django.contrib.auth.models import Permission

class PermissionCreateSerializer(serializers.Serializer):
    """
    Serializador para la creación dinámica de un nuevo permiso.

    Campos requeridos:
        - codename (str): Nombre corto único del permiso (ej. 'can_view_dashboard').
        - name (str): Nombre legible del permiso para mostrar en la UI.
        - content_type_app_label (str): Nombre de la app donde se aplicará el permiso.
        - content_type_model (str): Nombre del modelo al que se asociará el permiso.

    Ejemplo de payload:
    {
        "codename": "can_manage_inventory",
        "name": "Puede gestionar inventario",
        "content_type_app_label": "user",
        "content_type_model": "user"
    }
    """
    codename = serializers.CharField()
    name = serializers.CharField()
    content_type_app_label = serializers.CharField()
    content_type_model = serializers.CharField()


class AssignPermissionToGroupSerializer(serializers.Serializer):
    """
    Serializador para asignar permisos existentes a un grupo (rol).

    Campos requeridos:
        - group_name (str): Nombre del grupo al que se le asignarán los permisos.
        - permissions (list[str]): Lista de `codenames` de los permisos a asignar.

    Ejemplo de payload:
    {
        "group_name": "Administrador del sistema",
        "permissions": ["can_view_dashboard", "can_manage_roles"]
    }
    """
    group_name = serializers.CharField()
    permissions = serializers.ListField(
        child=serializers.CharField(),
        help_text="Lista de codenames de permisos a asignar"
    )

class ListPermissionSerializer(serializers.Serializer):
    '''
    Serializador utilizado para llamar los campos requeridos con la 
    información de cuales son los permisos en el sistema.

    Los campos que devolvera:
      - permissionId: integer Identificador único del Permiso. 
      - name: string Nombre del Permiso en BD.

      --Aquí tenemos problemas ya que no existe una tabla con estos campos-- 
      - label: string Nombre del Permiso para mostrar en el front.
      - description: string Descripción del Permiso.
      - createdAt: string Fecha de creación del Permiso.
      - updatedAt: string Fecha de la última modificación del Permiso.    
      
      Autor: [Fernando Octavio Arroyo Velaso]
      Fecha: [24 de julio 2025]
    '''
    permissionId = serializers.IntegerField(source = 'id')
    name = serializers.CharField()
    codename = serializers.CharField()
    
    #Campos que necesitamos procesar pero no se tienen en el modelo aún.
    description = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    updatedAt = serializers.SerializerMethodField()
    
    class Meta:
        model = Permission
        fields = ['permissionId', 
                  'name',
                  'codename',
                  'description',
                  'createdAt',
                  'updatedAt',  
                  ]
        
    #Esto nos sirve para regresar Node a los atributos no implementados para los permisos
    #Esto mas adelante se borrar y se tomaran los valortes reales de los mismos.
    def get_description(self, obj):
        return None

    def get_createdAt(self, obj):
        return None

    def get_updatedAt(self, obj):
        return None