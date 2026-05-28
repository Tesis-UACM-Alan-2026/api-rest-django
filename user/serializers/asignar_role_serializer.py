"""
Serializador para la asignación de roles a usuarios del sistema.

Este serializador valida y procesa las solicitudes de cambio de rol para usuarios
existentes en el sistema de gestión hospitalaria, asegurando que solo se asignen
roles válidos definidos en RoleChoices y proporcionando validación robusta.

Estructura:
- `AssignRoleSerializer`: Valida los datos requeridos para asignar un rol a un usuario.

Se utiliza en vistas específicas bajo `views/role_assign.py` y mejora la documentación
automática en Swagger mediante `@swagger_auto_schema`.

Autor: [Equipo de desarrollo HIMFG]
Fecha: [Última modificación: 01-ago-25]
"""

from rest_framework import serializers
from user.choices import RoleChoices

class AssignRoleSerializer(serializers.Serializer):
    """
    Serializador para la asignación de un rol específico a un usuario.

    Campos requeridos:
        - role (str): Identificador del rol según RoleChoices (ej. 'Solicitante', 'Administrador').

    Ejemplo de payload:
    [
        {
            "role": "Solicitante"
        }
    ]

    Validaciones aplicadas:
        - Verificación de existencia: El rol debe existir en RoleChoices.choices
        - Formato requerido: El campo role es obligatorio
        - Lista de opciones: Se proporciona lista completa de roles válidos en caso de error

    Notas:
        - Se utiliza con many=True para aceptar formato de array
        - Campo directo sin conversión camelCase/snake_case
        - Integrado con djangorestframework-camel-case para compatibilidad frontend
        - Los errores incluyen la lista completa de roles disponibles para facilitar depuración

    Autor: [Equipo de desarrollo HIMFG]
    Fecha: [01 de agosto 2025]
    """
    role = serializers.CharField(required=True)

    def validate_role(self, value):
        """
        Valida que el rol proporcionado sea uno de los roles válidos del sistema.

        Args:
            value (str): El identificador del rol a validar.

        Returns:
            str: El valor validado si es correcto.

        Raises:
            ValidationError: Si el rol no está en RoleChoices.choices,
                           incluyendo la lista completa de opciones disponibles.
        """
        valid_roles = [choice[0] for choice in RoleChoices.choices]
        if value not in valid_roles:
            raise serializers.ValidationError(f"El rol '{value}' no es válido. Debe ser uno de: {valid_roles}.")
        return value