from django.contrib.auth.models import Group
from django.db.models import TextChoices

class RoleChoices(TextChoices):
    """
    Enumeración de roles disponibles en el sistema, utilizados para asignar 
    permisos y agrupar usuarios dentro de la arquitectura de seguridad basada en grupos.

    Esta clase hereda de `TextChoices` de Django, lo que permite:
        - Usar los roles como `choices` en campos de modelo.
        - Acceder a sus valores de forma centralizada, evitando hardcodeo.
        - Integrarlos con el sistema de grupos (`Group`) de Django para control de acceso.

    Cada entrada tiene como valor y etiqueta la descripción textual del rol.
    """
    ADMIN = 'Administrador del sistema', 'Administrador del sistema'
    JEFE_DPTO_ALMACENES = 'Jefe del Departamento de Almacenes', 'Jefe del Departamento de Almacenes'
    SEGUNDO_DPTO_ALMACENES = 'Segundo encargado del Departamento de Almacenes', 'Segundo encargado del Departamento de Almacenes'
    JEFE_ROPERIA = 'Jefe del Almacén de Ropería', 'Jefe del Almacén de Ropería'
    SEGUNDO_ROPERIA = 'Segundo encargado del Almacén de Ropería', 'Segundo encargado del Almacén de Ropería'
    JEFE_VIVERES = 'Jefe del Almacén de Víveres', 'Jefe del Almacén de Víveres'
    SEGUNDO_VIVERES = 'Segundo encargado del Almacén de Víveres', 'Segundo encargado del Almacén de Víveres'
    JEFE_FARMACIA = 'Jefe del Almacén de Farmacia', 'Jefe del Almacén de Farmacia'
    SEGUNDO_FARMACIA = 'Segundo encargado Almacén de Farmacia', 'Segundo encargado Almacén de Farmacia'
    CAPTURISTA_ENTRADAS = 'Capturista de entradas', 'Capturista de entradas'
    CAPTURISTA_SALIDAS = 'Capturista de salidas', 'Capturista de salidas'
    SOLICITANTE = 'Solicitante', 'Solicitante'

def assign_user_to_role(user, role: str):
    """
    Asigna un usuario a un grupo (rol) determinado.

    Si el grupo especificado no existe, se crea automáticamente. Esta función 
    permite gestionar los roles del sistema de forma centralizada, evitando el 
    hardcodeo y asegurando que los usuarios pertenezcan al grupo correspondiente.

    Args:
        user (User): Instancia del modelo de usuario al que se le asignará el rol.
        role (str): Nombre del rol, correspondiente a un valor definido en RoleChoices.

    Raises:
        ValueError: Si el rol proporcionado no es válido.

    Returns:
        None
    """
    if not isinstance(role, RoleChoices):
        raise ValueError("El rol debe ser una instancia de RoleChoices.")
    group, _ = Group.objects.get_or_create(name=role.value)
    user.groups.add(group)
