import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_yasg.utils import swagger_auto_schema

from gestion_usuarios.DAO.usuarioDAO import UsuarioDAO
from gestion_usuarios.serializers import (
    UsuarioCompletoSerializer,
    UsuarioParcialSerializer,
    UsuarioContrasenaSerializer,
    PasswordResetRequestSerializer,
)
from gestion_usuarios.exceptions.usuarioExeptions import (
    UsuarioNoAutorizado_401,
    UsuarioProhibido_403,
    ErrorInternoServidor_500,
    UsuarioNoEncontrado_404,
    DatosInvalidos_400,
    ConflictoUsuario_409,
)

logger = logging.getLogger('gestion_permisos') #logs técnicos
logger_auditoria = logging.getLogger('auditoria') #logs de auditoría

def obtener_ip(request): #Nos permite obtener la IP real del cliente, incluso si está detrás de un proxy o balanceador de carga.
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'IP desconocida')


class PermisosViewSet(viewsets.ViewSet):
    pass