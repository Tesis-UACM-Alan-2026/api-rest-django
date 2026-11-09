import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from core.utils import obtener_ip, auditar
from autentificacion.service import AutenticacionService
from autentificacion.serializers import (
    LoginSerializer,
    SesionSerializer,
    LogoutSerializer,
)
from autentificacion.exceptions.autenticacionExceptions import (
    CredencialesInvalidas_401,
    TokenInvalido_400,
    TokenAjeno_403,
)

autenticacionService = AutenticacionService()

logger = logging.getLogger(__name__)  # logs técnicos


class LoginView(APIView):
    """
    Inicio de sesión con email y contraseña.
    Devuelve access y refresh token si las credenciales son válidas.
    """

    # Endpoint público. Sin autenticadores: si el cliente manda un token
    # vencido en la cabecera, no debe rechazarse el login por eso.
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Iniciar sesión",
        request_body=LoginSerializer,
        security=[],
        responses={
            200: SesionSerializer(),
            400: "Datos incompletos o inválidos.",
            401: "Credenciales inválidas.",
        },
    )
    def post(self, request):
        ip = obtener_ip(request)

        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            auditar(
                ip, "LOGIN_FALLIDO", None, nivel=logging.WARNING,
                detalle="credenciales incompletas"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            sesion = autenticacionService.iniciar_sesion(email, password, request)

        except CredencialesInvalidas_401 as error:
            auditar(
                ip, "LOGIN_FALLIDO", None, nivel=logging.WARNING,
                usuario=email, detalle="credenciales incorrectas"
            )
            return Response(
                {"error": str(error)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        auditar(ip, "LOGIN_EXITOSO", None, usuario=sesion.email, id=sesion.usuario_id)

        return Response(SesionSerializer(sesion).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Cierre de sesión: invalida el refresh token añadiéndolo a la blacklist.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Cerrar sesión",
        request_body=LogoutSerializer,
        responses={
            200: "Sesión cerrada correctamente.",
            400: "Token inválido o ya expirado.",
            401: "No autenticado.",
            403: "El token no pertenece al usuario autenticado.",
        },
    )
    def post(self, request):
        ip = obtener_ip(request)

        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario = request.user

        try:
            autenticacionService.cerrar_sesion(
                usuario.id,
                serializer.validated_data["refresh"]
            )

            auditar(ip, "LOGOUT", None, usuario=usuario.email, id=usuario.id)

            return Response(
                {"mensaje": "Sesión cerrada correctamente."},
                status=status.HTTP_200_OK
            )

        except TokenInvalido_400 as error:
            logger.warning(f"Logout fallido para {usuario.email}: {error}")
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except TokenAjeno_403 as error:
            auditar(
                ip, "LOGOUT_TOKEN_AJENO", None, nivel=logging.WARNING,
                usuario=usuario.email, id=usuario.id
            )
            return Response(
                {"error": str(error)},
                status=status.HTTP_403_FORBIDDEN
            )