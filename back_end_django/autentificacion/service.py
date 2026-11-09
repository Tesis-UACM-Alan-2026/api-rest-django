from django.contrib.auth import authenticate

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from autentificacion.VO.sesionVO import SesionVO
from autentificacion.VO.logVO import LogConsultaVO
from autentificacion.DAO.logDAO import LogDAO
from autentificacion.exceptions.autenticacionExceptions import (
    CredencialesInvalidas_401,
    TokenInvalido_400,
    TokenAjeno_403,
)


class AutenticacionService:
    """
    Inicio y cierre de sesión con JWT.
    Las excepciones se propagan a la vista, que las traduce a HTTP.
    """

    def iniciar_sesion(self, email: str, password: str, request=None) -> SesionVO:
        # authenticate() rechaza usuarios inactivos (ModelBackend) y verifica
        # la contraseña una sola vez.
        usuario = authenticate(request=request, email=email, password=password)

        if usuario is None or not usuario.is_active:
            raise CredencialesInvalidas_401()

        refresh = RefreshToken.for_user(usuario)

        return SesionVO(
            access=str(refresh.access_token),
            refresh=str(refresh),
            usuario_id=usuario.id,
            email=usuario.email,
        )

    def cerrar_sesion(self, usuario_id, refresh_token: str) -> None:
        """Invalida (blacklist) el refresh token, solo si es del propio usuario."""
        try:
            token = RefreshToken(refresh_token)
        except TokenError:
            raise TokenInvalido_400()

        if str(token.get(api_settings.USER_ID_CLAIM)) != str(usuario_id):
            raise TokenAjeno_403()

        try:
            token.blacklist()
        except TokenError:
            raise TokenInvalido_400()


class LogService:
    """Consulta de los registros de auditoría y técnicos."""

    def consultar(self, tipo: str, filtros: dict, limite: int) -> LogConsultaVO:
        entradas = LogDAO.leer(tipo, filtros=filtros, limite=limite)

        return LogConsultaVO(
            total=len(entradas),
            filtros_aplicados={k: v for k, v in filtros.items() if v},
            entradas=entradas,
        )